import os
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
import pandas as pd

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
def clean_title(title):
    # Normalize unicode (useful for Hebrew and mixed characters)
    title = unicodedata.normalize("NFKC", title or "")
    title = re.sub(r"[^\w\s]", "", title)   # Remove punctuation
    title = re.sub(r"\s+", " ", title)      # Collapse whitespace
    return title.strip().lower()

def normalize_summary(text):
    text = text or ""
    if isinstance(text, str):
        text = re.sub(r"\s+", " ", text).strip()
    else:
        text = ""
    return text

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

"""
Preprocess each record:
- Add a cleaned version of the title
- Parse ISO timestamp into datetime object
- Generate a deduplication key using clean title + date
- Filter out obviously bad/category-only titles
"""
def preprocess(records):
    cleaned = []

    for record in records:
        # 1. Skip if title is missing/empty or is a category label
        raw_title = record.get("title")
        if not raw_title or raw_title.strip() == "" or raw_title.strip() in CATEGORY_TITLES:
            continue  # title is required and must be a real headline

        # 1.1 Normalize summary whitespace; allow empty summary, but not None
        record["summary"] = normalize_summary(record.get("summary"))

        # 2. Clean title
        record["clean_title"] = clean_title(raw_title)

        # 3. Handle published_iso
        iso_str = record.get("published_iso")
        if isinstance(iso_str, str):
            try:
                record["published_dt"] = datetime.fromisoformat(iso_str)
            except ValueError:
                record["published_dt"] = None
                record["published_iso"] = ""
        else:
            record["published_dt"] = None
            record["published_iso"] = ""

        # 4. Set dedup_key
        if record["published_dt"]:
            date_str = record["published_dt"].date()
        else:
            date_str = "no-date"

        record["dedup_key"] = f"{record['clean_title']}_{date_str}"

        # 5. Append cleaned record
        cleaned.append(record)

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
