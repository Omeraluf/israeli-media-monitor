# preprocessing/dataframe_hygiene.py
from typing import List, Dict

def dataframe_hygiene(records: List[Dict]) -> List[Dict]:
    """Drop exact duplicates by record_key; keep first occurrence."""
    seen = set()
    out = []
    for r in records:
        k = r.get("record_key")
        if not k:
            out.append(r)            # if no key, keep it (rare)
            continue
        if k in seen:
            continue                 # drop dup
        seen.add(k)
        out.append(r)
    return out
