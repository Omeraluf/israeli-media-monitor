import os
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
import pandas as pd
from analysis.utils.time_labels import is_time_label

# ===== Config =====
CATEGORY_TITLES = {
    "אוכל", "תרבות", "תרבות ובידור", "חדשות", "ספורט", "דעה", "מבזק"
}
BOILERPLATE_MIN_COUNT = 5       # summaries repeating at least this many times...
BOILERPLATE_MIN_RATIO = 0.5     # ...and comprising at least this fraction of a source

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ===== Helpers =====
SEP = r"[|/:;·•–—\-‑‒―־]+"
BULLETS = r"[•\u2022]"
def sanitize_for_display(text: str) -> str:
    if not isinstance(text, str): return ""
    s = unicodedata.normalize("NFKC", text)
    s = re.sub(SEP, " ", s)
    s = re.sub(BULLETS, " ", s)
    s = "".join(ch for ch in s if unicodedata.category(ch)[0] not in ("P","S"))
    s = re.sub(r"\s+", " ", s).strip()
    return s

def clean_title(title):
    # Normalize unicode (useful for Hebrew and mixed characters)
    title = unicodedata.normalize("NFKC", title or "")
    title = re.sub(r"[^\w\s]", "", title)   # Remove punctuation
    title = re.sub(r"\s+", " ", title)      # Collapse whitespace
    return title.strip().lower()

def normalize_summary(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"[•\u2022]", " ", text)   # drop bullet chars
    text = re.sub(r"\s+", " ", text)         # collapse whitespace
    return text.strip()


"""
Load all JSON files from the raw data directory.
Supports both single-item and list-of-items JSON structures.
Returns a combined list of records.
"""
def load_raw_json_files():
    all_records = []
    for file in RAW_DIR.glob("*.json"):
        with open(file, encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                all_records.extend(data)
            else:
                all_records.append(data)
    return all_records

# --- put near your other helpers (top of file) ---
from collections import Counter, defaultdict

def drop_boilerplate_summaries(records, *, min_count: int = 5, min_ratio: float = 0.5, keep_last_dup: bool = True):
    """
    Per-source cleanup:
      1) If a summary text appears very frequently for a source (>= min_count and covers >= min_ratio of that source),
         treat it as boilerplate and blank it.
      2) Optionally keep only the *last* occurrence of any repeated summary text per source (blank earlier ones).
    Assumes each record has 'source', 'summary' and 'summary_sanitized'.
    """
    by_source = defaultdict(list)
    for i, r in enumerate(records):
        r["_idx"] = i  # stable position (for 'last' logic)
        by_source[r.get("source", "")].append(r)

    for src, rows in by_source.items():
        texts = [(r.get("summary_sanitized", "") or "") for r in rows]
        n = len(rows)
        freq = Counter([t for t in texts if t])
        boiler = {t for t, c in freq.items() if c >= min_count and (c / max(n, 1)) >= min_ratio}

        # 1) drop boilerplate summaries
        for r in rows:
            if (r.get("summary_sanitized", "") or "") in boiler:
                r["summary"] = ""
                r["summary_sanitized"] = ""

        if keep_last_dup:
            # keep only the last occurrence of each summary text per source
            last_idx = {}
            for r in rows:
                s = r.get("summary_sanitized", "") or ""
                if s:
                    last_idx[s] = r["_idx"]
            for r in rows:
                s = r.get("summary_sanitized", "") or ""
                if s and last_idx.get(s) != r["_idx"]:
                    r["summary"] = ""
                    r["summary_sanitized"] = ""

    for r in records:
        r.pop("_idx", None)
    return records


"""
Preprocess each record:
- Add a cleaned version of the title
- Parse ISO timestamp into datetime object
- Generate a deduplication key using clean title + date
- Filter out obviously bad/category-only titles
"""
# --- replace your preprocess() with this ---
def preprocess(records):
    cleaned = []

    for record in records:
        # 1) Skip if title is missing/empty or is a category label
        raw_title = record.get("title")
        if not raw_title or raw_title.strip() == "" or raw_title.strip() in CATEGORY_TITLES:
            continue

        # 2) Titles: preserve original, create sanitized (for display/clustering), and clean_title (for keys)
        record["original_title"] = raw_title or ""
        record["title_sanitized"] = sanitize_for_display(record["original_title"])
        record["title"] = record["title_sanitized"]                  # use sanitized by default
        record["clean_title"] = clean_title(record["original_title"]) # lowercase, machine-friendly

        # 3) Summaries: drop time labels, then normalize + sanitize
        raw_summary = record.get("summary") or ""
        if is_time_label(raw_summary):
            record["summary"] = ""
        else:
            record["summary"] = normalize_summary(raw_summary)
        record["summary_sanitized"] = sanitize_for_display(record["summary"])

        # 4) published_iso -> published_dt (best-effort)
        iso_str = record.get("published_iso")
        if isinstance(iso_str, str) and iso_str.strip():
            try:
                record["published_dt"] = datetime.fromisoformat(iso_str)
            except ValueError:
                record["published_dt"] = None
                record["published_iso"] = ""
        else:
            record["published_dt"] = None
            record["published_iso"] = ""

        # 5) dedup_key: clean_title + date/no-date
        date_part = record["published_dt"].date() if record["published_dt"] else "no-date"
        record["dedup_key"] = f"{record['clean_title']}_{date_part}"

        cleaned.append(record)

    # 6) Per-source summary hygiene (C14 issue): drop boilerplate & keep only last occurrence of repeated summaries
    cleaned = drop_boilerplate_summaries(cleaned, min_count=5, min_ratio=0.5, keep_last_dup=True)

    return cleaned



# ===== DataFrame Hygiene =====
def dataframe_hygiene(records):
    """
    Apply DataFrame-level hygiene:
    - Drop category-only titles (extra safety)
    - Remove boilerplate summaries that repeat too often within the same source
    - Drop duplicate URLs
    - Rebuild normalized summary, clean_title, and dedup_key
    """
    if not records:
        return records

    df = pd.DataFrame(records)

    # Ensure expected columns exist
    for col in ["title", "summary", "source", "url", "published_dt"]:
        if col not in df.columns:
            df[col] = None

    # 1) Drop category-only titles (exact match after strip)
    mask_category = df["title"].astype(str).str.strip().isin(CATEGORY_TITLES)
    before = len(df)
    df = df[~mask_category].copy()

    # 2) Remove boilerplate summaries per source
    #    Identify (source, summary) pairs that repeat "too often"
    df["summary"] = df["summary"].apply(normalize_summary)
    # Ignore empty summaries in boilerplate detection
    non_empty = df["summary"].astype(str).str.len() > 0
    counts = (
        df[non_empty]
        .groupby(["source", "summary"], dropna=False)
        .size()
        .reset_index(name="count")
    )
    totals = df.groupby("source", dropna=False).size().reset_index(name="total")

    freq = counts.merge(totals, on="source", how="left")
    freq["ratio"] = freq["count"] / freq["total"].where(freq["total"] != 0, 1)

    boilerplate_pairs = set(
        tuple(x)
        for x in freq[
            (freq["count"] >= BOILERPLATE_MIN_COUNT) & (freq["ratio"] >= BOILERPLATE_MIN_RATIO)
        ][["source", "summary"]].to_records(index=False)
    )

    if boilerplate_pairs:
        bp_mask = df.apply(
            lambda r: (r["source"], r["summary"]) in boilerplate_pairs, axis=1
        )
        df = df[~bp_mask].copy()

    # 3) Drop duplicates per URL (keep first)
    if "url" in df.columns:
        # Keep rows with missing URL intact but drop duplicate non-null URLs
        df = df.sort_index()  # keep original order
        non_null = df["url"].notna() & df["url"].astype(str).str.len().gt(0)
        deduped = pd.concat([
            df[non_null].drop_duplicates(subset=["url"], keep="first"),
            df[~non_null]
        ]).sort_index()
        df = deduped

    # 4) Rebuild normalized summary, clean_title, and dedup_key
    df["summary"] = df["summary"].apply(normalize_summary)
    df["clean_title"] = df["title"].astype(str).apply(clean_title)

    def make_dedup_key(row):
        dt = row.get("published_dt")
        if isinstance(dt, datetime):
            date_str = dt.date()
        else:
            date_str = "no-date"
        return f"{row['clean_title']}_{date_str}"

    df["dedup_key"] = df.apply(make_dedup_key, axis=1)

    # Return to list[dict] with Python types intact
    return df.to_dict(orient="records")


"""
Save the preprocessed records to a JSON file in the processed data folder,
with a filename based on today's date.
"""
def save_processed(records):
    today = datetime.now().strftime("%Y-%m-%d")
    output_path = PROCESSED_DIR / f"combined_{today}.json"

    # Convert datetimes back to ISO strings
    for record in records:
        if isinstance(record.get("published_dt"), datetime):
            record["published_dt"] = record["published_dt"].isoformat()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"Saved processed data to {output_path}")

def main():
    """
    Main entry point:
    - Load raw scraped data
    - Preprocess all records
    - Apply DataFrame hygiene (category-only titles, boilerplate summaries, URL dedup, rebuild keys)
    - Save the cleaned dataset
    """
    print("Loading raw data...")
    raw_records = load_raw_json_files()
    print(f"Found {len(raw_records)} records.")

    print("Preprocessing...")
    cleaned_records = preprocess(raw_records)
    print(f"After preprocess: {len(cleaned_records)} records "
          f"(discarded {len(raw_records) - len(cleaned_records)}).")

    print("Applying DataFrame hygiene...")
    before_hygiene = len(cleaned_records)
    cleaned_records = dataframe_hygiene(cleaned_records)
    print(f"After hygiene: {len(cleaned_records)} records "
          f"(discarded {before_hygiene - len(cleaned_records)} more).")

    print("Saving cleaned data...")
    save_processed(cleaned_records)
    print("Preprocessing complete.")

if __name__ == "__main__":
    main()
