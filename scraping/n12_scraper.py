import feedparser
import json
import os
from datetime import datetime
from time import mktime

def get_n12_rss_headlines():
    url = "https://rcs.mako.co.il/rss/news-israel.xml"
    feed = feedparser.parse(url)

    headlines = []

    print(feed.entries[0].published_parsed)  # Print all keys in the first entry for debugging

    for entry in feed.entries:
        # Convert published_parsed → datetime object
        published_dt = (
            datetime.fromtimestamp(mktime(entry.get("published_parsed")))
            if entry.get("published_parsed") else None
        )

        #Safer with .get() to avoid KeyError if key is missing
        headlines.append({
            "title": entry.get("title", ""),
            "summary": entry.get("shortdescription", entry.get("summary", "")),
            "url": entry.get("link", ""),
            "published": entry.get("published", None),
            "published_iso": published_dt.isoformat() if published_dt else "",
            "source": "n12",
            "scraped_at": datetime.now().isoformat()
        })
        # print(entry.title[::-1] if 'published' in entry else None)  #only for debugging and reading hebrew on terminal (RTL)

    os.makedirs("data/raw", exist_ok=True)
    filename = f"data/raw/n12_rss_{datetime.now().date()}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(headlines, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(headlines)} headlines to {filename}")
    return headlines
