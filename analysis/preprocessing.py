import os
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def clean_title(title):
    # Normalize unicode (useful for Hebrew and mixed characters)
    title = unicodedata.normalize("NFKC", title)
    title = re.sub(r'[^\w\s]', '', title)  # Remove punctuation
    title = re.sub(r'\s+', ' ', title)  # Collapse whitespace
    return title.strip().lower()

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
"""
def preprocess(records):
    cleaned = []

    for record in records:
        # 1. Skip if title is missing or empty
        raw_title = record.get("title")
        if not raw_title or raw_title.strip() == "":
            continue  # title is required, discard record

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


"""
Save the preprocessed records to a JSON file in the processed data folder,
with a filename based on today's date.
"""
def save_processed(records):
    today = datetime.now().strftime("%Y-%m-%d")
    output_path = PROCESSED_DIR / f"combined_{today}.json"
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
    - Save the cleaned dataset
    """
    print("Loading raw data...")
    raw_records = load_raw_json_files()
    print(f"Found {len(raw_records)} records.")

    print("Preprocessing...")
    cleaned_records = preprocess(raw_records)

    discarded = len(raw_records) - len(cleaned_records)
    print(f"Cleaned {len(cleaned_records)} records. Discarded: {discarded}.")

    print("Saving cleaned data...")
    save_processed(cleaned_records)
    print("Preprocessing complete.")

if __name__ == "__main__":
    main()
