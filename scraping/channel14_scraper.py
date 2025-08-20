# ## old one, kept for reference - works kinga good - bad summary
# import requests
# from bs4 import BeautifulSoup
# import json
# import os
# from datetime import datetime
# from urllib.parse import urljoin
# from datetime import timedelta

# def parse_hebrew_time(text):
#     now = datetime.now()

#     if "לפני" in text:
#         if "דקה" in text:
#             return (now - timedelta(minutes=1)).isoformat()
#         elif "דקות" in text:
#             num = int(''.join(filter(str.isdigit, text)) or 0)
#             return (now - timedelta(minutes=num)).isoformat()
#         elif "שעה" in text:
#             return (now - timedelta(hours=1)).isoformat()
#         elif "שעתיים" in text:
#             return (now - timedelta(hours=2)).isoformat()
#         elif "שעות" in text:
#             num = int(''.join(filter(str.isdigit, text)) or 0)
#             return (now - timedelta(hours=num)).isoformat()
#     elif "אתמול" in text:
#         # Try to extract hour from format like 'אתמול 23:01'
#         parts = text.replace("אתמול", "").strip().split(":")
#         if len(parts) == 2:
#             try:
#                 hour, minute = int(parts[0]), int(parts[1])
#                 dt = now - timedelta(days=1)
#                 dt = dt.replace(hour=hour, minute=minute, second=0, microsecond=0)
#                 return dt.isoformat()
#             except:
#                 pass
#         else:
#             return (now - timedelta(days=1)).isoformat()

#     return None  # Fallback if we can't parse

# # def get_c14_headlines():
# #     url = "https://www.c14.co.il/"
# #     response = requests.get(url)
# #     response.encoding = 'utf-8'  # Ensure Hebrew displays correctly

# #     if response.status_code != 200:
# #         print(f"Failed to fetch page: {response.status_code}")
# #         return []

# #     soup = BeautifulSoup(response.text, "html.parser")

# #     headlines = []
# #     for tag in soup.find_all(['h1', 'h2']):
# #             title = tag.get_text(strip=True)

# #             # Find summary
# #             summary_tag = tag.find_next('p')
# #             summary = summary_tag.get_text(strip=True) if summary_tag else ""

# #             # Find published (next <p> after summary)
# #             published_tag = summary_tag.find_next('p') if summary_tag else None
# #             published = published_tag.get_text(strip=True) if published_tag else ""

# #             # Find URL if <a> is a parent or sibling
# #             a_tag = tag.find_parent('a') or tag.find_next('a')
# #             url = urljoin(url, a_tag['href']) if a_tag and a_tag.get('href') else ""

# #             headlines.append({
# #                 "title": title,
# #                 "summary": summary,
# #                 "url": url,
# #                 "published": published,
# #                 "published_iso": parse_hebrew_time(published),      #raw
# #                 "source": "channel14",
# #                 "scraped_at": datetime.now().isoformat()
# #             })

# #     os.makedirs("data/raw", exist_ok=True)

# #     filename = f"data/raw/c14_scraped_{datetime.now().date()}.json"
# #     with open(filename, "w", encoding="utf-8") as f:
# #         json.dump(headlines, f, ensure_ascii=False, indent=2)

# #     print(f"Saved {len(headlines)} headlines to {filename}")


# -*- coding: utf-8 -*-
import os
import json
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin
from analysis.utils.time_labels import is_time_label

import requests
from bs4 import BeautifulSoup

# --- Generic time-label detection & parsing (Hebrew + basic English) ---

DEFAULT_TZ = timezone(timedelta(hours=3))  # Asia/Jerusalem (simple, 3.8-friendly)

_CLOCK = re.compile(r"^\s*\d{1,2}[:.]\d{2}\s*$")          # "10:22" or "10.22"
_ONLY_DIGITS_SEPARATORS = re.compile(r"^[\s\d:.\-/]+$")   # very short "21:03", "12/08", etc.

_LOCALE = {
    "he": {
        "yesterday": ["אתמול"],
        "ago_prefix": ["לפני"],  # Hebrew "ago" is a prefix
        "units": {
            "minute": ["דקה", "דקות"],
            "hour": ["שעה", "שעות", "כשעה", "שעתיים"],
            "day": ["יום", "ימים", "יומיים"],
        },
    },
    "en": {
        "yesterday": ["yesterday"],
        "ago_prefix": ["ago"],  # usually suffix in English, we handle both
        "units": {
            "minute": ["minute", "minutes", "min", "mins"],
            "hour": ["hour", "hours", "hr", "hrs"],
            "day": ["day", "days"],
        },
    },
}

def _guess_locale(s: str) -> str:
    # crude but effective: if any Hebrew char -> Hebrew
    if any("\u0590" <= ch <= "\u05FF" for ch in s):
        return "he"
    return "en"

def parse_hebrew_time(text: str) -> str or None:
    """
    Backwards-compatible name with your original signature.
    Parses Hebrew/English-like time labels into tz-aware ISO string.
    Returns None if not confidently parseable.

    Supports:
      - "HH:MM" or "HH.MM" (today at that time)
      - "אתמול HH:MM" / "yesterday HH:MM"
      - "אתמול" / "yesterday" (same time, minus one day)
      - "לפני 5 דקות/שעות/ימים", "5 minutes ago", "2 hours ago"
    """
    if not isinstance(text, str):
        return None
    s = text.strip()
    if not s:
        return None

    now = datetime.now(DEFAULT_TZ)
    loc = _guess_locale(s)
    L = _LOCALE.get(loc, _LOCALE["en"])
    s_low = s.lower()

    # 1) Exact clock "HH:MM" or "HH.MM"
    m = re.fullmatch(r"(\d{1,2})[:.](\d{2})", s)
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
        dt = now.replace(hour=h, minute=mi, second=0, microsecond=0)
        return dt.isoformat()

    # 2) Yesterday with/without time
    if any(word in s_low for word in L["yesterday"]):
        tm = re.search(r"(\d{1,2})[:.](\d{2})", s)
        dt = now - timedelta(days=1)
        if tm:
            h, mi = int(tm.group(1)), int(tm.group(2))
            dt = dt.replace(hour=h, minute=mi, second=0, microsecond=0)
        return dt.isoformat()

    # 3) Relative “ago” / "לפני ..."
    # extract a number if present, default to 1
    num_match = re.search(r"(\d+)", s)
    n = int(num_match.group(1)) if num_match else 1

    def has_any(keys):
        return any(any(u in s for u in L["units"][k]) for k in keys)

    # Hebrew idioms
    if loc == "he" and "שעתיים" in s:
        return (now - timedelta(hours=2)).isoformat()
    if loc == "he" and "יומיים" in s:
        return (now - timedelta(days=2)).isoformat()

    ago_hit = any(tok in s for tok in L["ago_prefix"])

    if has_any(["minute"]) and (ago_hit or loc == "he"):
        return (now - timedelta(minutes=n)).isoformat()
    if has_any(["hour"]) and (ago_hit or loc == "he"):
        return (now - timedelta(hours=n)).isoformat()
    if has_any(["day"]) and (ago_hit or loc == "he"):
        return (now - timedelta(days=n)).isoformat()

    return None

# --- Channel 14 scraper (source-agnostic summary/published handling) ---

def get_c14_headlines():
    base = "https://www.c14.co.il/"
    try:
        resp = requests.get(base, timeout=15)
    except requests.RequestException as e:
        print(f"Failed to fetch page: {e}")
        return []

    resp.encoding = "utf-8"
    if resp.status_code != 200:
        print(f"Failed to fetch page: {resp.status_code}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    now = datetime.now(DEFAULT_TZ)

    headlines = []
    for tag in soup.find_all(["h1", "h2"]):
        title = (tag.get_text(strip=True) or "").strip()
        if not title:
            continue

        # URL from parent/sibling <a>
        a_tag = tag.find_parent("a") or tag.find_next("a")
        href = a_tag.get("href") if a_tag else ""
        url = urljoin(base, href) if href else ""

        # Candidate <p> blocks near the header
        p1 = tag.find_next("p")
        p1_text = (p1.get_text(strip=True) if p1 else "").strip()

        # Decide summary vs time label
        if is_time_label(p1_text):
            summary = ""
            published_text = p1_text
        else:
            summary = p1_text
            published_text = ""

        # If we didn't find a time label yet, check the next <p>
        if not published_text:
            p2 = p1.find_next("p") if p1 else None
            p2_text = (p2.get_text(strip=True) if p2 else "").strip()
            if is_time_label(p2_text):
                published_text = p2_text
            elif not summary and p2_text and not is_time_label(p2_text):
                # If summary was empty and p2 looks like content, use it
                summary = p2_text

        published_iso = parse_hebrew_time(published_text) if published_text else None

        headlines.append({
            "title": title,
            "summary": summary,                      # blank if it's a time label
            "url": url,
            "published": published_text,             # keep raw label for debugging (optional)
            "published_iso": published_iso or "",    # ISO or empty
            "source": "c14",
            "scraped_at": now.isoformat(),
        })

    os.makedirs("data/raw", exist_ok=True)
    out_fn = f"data/raw/c14_scraped_{now.date()}.json"
    with open(out_fn, "w", encoding="utf-8") as f:
        json.dump(headlines, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(headlines)} headlines to {out_fn}")
    return headlines
