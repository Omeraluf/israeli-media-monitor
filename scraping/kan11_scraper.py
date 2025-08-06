import feedparser
import json
import os
from datetime import datetime
from time import mktime

def get_kan11_rss_headlines():
    url = "https://www.kan.org.il/rss/news.xml"  # Main news RSS
    feed = feedparser.parse(url)

    headlines = []

    for entry in feed.entries:
        published_dt = (
            datetime.fromtimestamp(mktime(entry.get("published_parsed")))
            if entry.get("published_parsed") else None
        )

        headlines.append({
            "title": entry.get("title", ""),
            "summary": entry.get("summary", ""),
            "url": entry.get("link", ""),
            "published": entry.get("published", None),
            "published_iso": published_dt.isoformat() if published_dt else None,
            "source": "kan11",
            "scraped_at": datetime.now().isoformat()
        })

    os.makedirs("data/raw", exist_ok=True)
    filename = f"data/raw/kan11_rss_{datetime.now().date()}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(headlines, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(headlines)} headlines to {filename}")
    return headlines
