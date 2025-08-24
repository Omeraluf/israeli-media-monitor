import json
import os
import glob
from datetime import datetime
from analysis.utils.time_labels import is_time_label, parse_hebrew_time_label

raw_dir = "data/raw"
out_dir = "data/adapted"

# # If we didn't find a time label yet, check the next <p>
# if not published_text:
#     p2 = p1.find_next("p") if p1 else None
#     p2_text = (p2.get_text(strip=True) if p2 else "").strip()
#     if is_time_label(p2_text):
#         published_text = p2_text
#     elif not summary and p2_text and not is_time_label(p2_text):
#         # If summary was empty and p2 looks like content, use it
#         summary = p2_text            


# published_iso = parse_hebrew_time(published_text_raw) if published_text_raw else None

def adapt_records(raw_records):
    out = []
    for record in raw_records:
        published = record.get("published", "").strip()
        if is_time_label(published):
            print("------------------- Time LABEL Detected -------------------")
            published_iso = parse_hebrew_time_label(published, now=datetime.fromisoformat(record["scraped_at"]))
            print(f"Parsed to ISO: {published_iso}")
            print("-----------------------------------------------------------")
        else:
            print(f"Warning: unexpected published label (not a time label): '{published}' ############## FIX ME! ##############")
            published_iso = ""

        record["published_iso"] = published_iso
        out.append(record)
    return out

### MAIN ###
def main():
    # 1) Load raw data
    for in_path in glob.glob(os.path.join(raw_dir, "c14_scraped_*.json")):
        with open(in_path, "r", encoding="utf-8") as f:
            raw_records = json.load(f)      #list of dicts
    
    # 2) Adapt each record
        adapt_records = adapt_records(raw_records)

     # 3) decide output filename
        filename = os.path.basename(in_path).replace("scraped_", "adapted_")
        out_path = os.path.join(out_dir, filename)
    
     # 4) save
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(adapt_records, f, ensure_ascii=False, indent=2)
    
    print(f"C14 Adapted data saved to {out_path}")


    
## Ideal output example:
# {
#   "published": "לפני 3 שעות",
#   "published_iso": "2025-07-28T20:00:00+03:00",
#   "scraped_at": "2025-07-28T23:00:00+03:00"
# }

#  {
#     "title": "\"אם רוצים להכניע את חמאס - צריך להכריע, לא להמתין לעסקה\"",
#     "summary": "מפקד סיירת גולני לשעבר מזהיר: כל עיכוב מגדיל את מחיר המלחמה",
#     "url": "https://www.c14.co.il/article/1302342",
#     "published": "לפני כשעה",
#     "published_iso": "",
#     "source": "c14",
#     "scraped_at": "2025-08-24T14:39:09.334308+03:00"
#   },



    

if __name__ == "__main__":
    main()