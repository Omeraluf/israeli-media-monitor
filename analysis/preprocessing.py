# preprocessing/preprocess.py
from __future__ import annotations
from typing import Dict, List
from pathlib import Path
import json
from datetime import date

from adapters.common.url_utils import (
    canonicalize_url,
    extract_url_id,
    build_record_key,
    normalize_text
)
from analysis.dataframe_hygiene import dataframe_hygiene
from analysis.text_norm import norm_min

Record = Dict[str, object]

def preprocess(records: List[Record]) -> List[Record]:
    out: List[Record] = []
    for r in records or []:
        rec = dict(r)
        source = str(rec.get("source") or "").strip().lower()
        raw_url = str(rec.get("url") or "")
        can_url = canonicalize_url(raw_url)
        url_id = extract_url_id(can_url, source=source)

        # Normalize title & summary here
        title = rec.get("title", "")
        summary = rec.get("summary", "")
        rec["title"] = normalize_text(title)
        rec["summary"] = normalize_text(summary)
        rec["title_norm_min"] = norm_min(title)
        rec["summary_norm_min"] = norm_min(summary)

        record_key = build_record_key(source, can_url, url_id)

        rec["url"] = can_url
        rec["url_id"] = url_id
        rec["record_key"] = record_key
        out.append(rec)
    return out


# --- quick demo runner using your 2 JSON files ---
def main():
    import json, re
    from pathlib import Path
    from typing import Dict, List
    # make sure this import is at the top of the module in your file:
    # from preprocessing.preprocess import preprocess

    n12_dir = Path("data/raw")
    c14_dir = Path("data/adapted")
    out_dir = Path("data/processed")
    out_dir.mkdir(parents=True, exist_ok=True)

    date_pat = re.compile(r"\d{4}-\d{2}-\d{2}$")

    def extract_date(p: Path) -> str | None:
        token = p.stem.split("_")[-1]
        return token if date_pat.fullmatch(token) else None

    # collect files
    c14_files = sorted(c14_dir.glob("c14_adapted_*.json"))
    n12_files = sorted(n12_dir.glob("n12_rss_*.json"))
    all_files = c14_files + n12_files

    # group by date
    groups: Dict[str, List[Path]] = {}
    for f in all_files:
        d = extract_date(f)
        if not d:
            print(f"Skipping (no date found): {f.name}")
            continue
        groups.setdefault(d, []).append(f)

    if not groups:
        print("No input files found.")
        return

    # process each date separately
    for d in sorted(groups.keys()):
        files = groups[d]
        records: List[dict] = []

        for f in files:
            try:
                with f.open(encoding="utf-8") as fh:
                    data = json.load(fh)
                if isinstance(data, list):
                    records.extend(data)
                    print(f"[{d}] Loaded {len(data):4d} from {f.name}")
                else:
                    print(f"[{d}] Skipped (not a list): {f.name}")
            except Exception as e:
                print(f"[{d}] Failed to load {f.name}: {e}")

        if not records:
            print(f"[{d}] No records to process.")
            continue

        processed = preprocess(records)
        cleaned = dataframe_hygiene(processed)

        out_file = out_dir / f"combined_{d}.json"
        with out_file.open("w", encoding="utf-8") as fh:
            json.dump(cleaned, fh, ensure_ascii=False, indent=2)
        print(f"[{d}] records loaded: {len(records)}, after preprocess: {len(processed)}, after dedup: {len(cleaned)}")





if __name__ == "__main__":
    main()

