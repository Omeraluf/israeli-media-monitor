import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

PROCESSED_DIR = Path("data/processed")
FINAL_DIR = Path("data/final")
FINAL_DIR.mkdir(parents=True, exist_ok=True)

def load_processed_file():
    today = datetime.now().strftime("%Y-%m-%d")
    file_path = PROCESSED_DIR / f"combined_{today}.json"
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)

def deduplicate(records):
    """
    Deduplicate articles by dedup_key.
    Keeps only one representative per group.
    """
    grouped = defaultdict(list)

    # Group by dedup_key
    for record in records:
        key = record.get("dedup_key")
        grouped[key].append(record)

    deduplicated = []
    for key, group in grouped.items():
        # For now, just pick the first one as representative
        representative = group[0]
        deduplicated.append(representative)

    return deduplicated

def save_final(records):
    today = datetime.now().strftime("%Y-%m-%d")
    output_path = FINAL_DIR / f"combined_deduplicated_{today}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"Saved deduplicated output to {output_path}")

def main():
    print("Loading processed data...")
    records = load_processed_file()
    print(f"Loaded {len(records)} records.")

    print("Running exact deduplication...")
    unique = deduplicate(records)
    print(f"Found {len(unique)} unique records after deduplication.")

    print("Saving results...")
    save_final(unique)

if __name__ == "__main__":
    main()
