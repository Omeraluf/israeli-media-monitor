import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
from urllib.parse import urljoin
from datetime import timedelta

def parse_hebrew_time(text):
    now = datetime.now()

    if "לפני" in text:
        if "דקה" in text:
            return (now - timedelta(minutes=1)).isoformat()
        elif "דקות" in text:
            num = int(''.join(filter(str.isdigit, text)) or 0)
            return (now - timedelta(minutes=num)).isoformat()
        elif "שעה" in text:
            return (now - timedelta(hours=1)).isoformat()
        elif "שעתיים" in text:
            return (now - timedelta(hours=2)).isoformat()
        elif "שעות" in text:
            num = int(''.join(filter(str.isdigit, text)) or 0)
            return (now - timedelta(hours=num)).isoformat()
    elif "אתמול" in text:
        # Try to extract hour from format like 'אתמול 23:01'
        parts = text.replace("אתמול", "").strip().split(":")
        if len(parts) == 2:
            try:
                hour, minute = int(parts[0]), int(parts[1])
                dt = now - timedelta(days=1)
                dt = dt.replace(hour=hour, minute=minute, second=0, microsecond=0)
                return dt.isoformat()
            except:
                pass
        else:
            return (now - timedelta(days=1)).isoformat()

    return None  # Fallback if we can't parse


def get_c14_headlines():
    url = "https://www.c14.co.il/"
    response = requests.get(url)
    response.encoding = 'utf-8'  # Ensure Hebrew displays correctly

    if response.status_code != 200:
        print(f"Failed to fetch page: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    headlines = []
    for tag in soup.find_all(['h1', 'h2']):
            title = tag.get_text(strip=True)

            # Find summary
            summary_tag = tag.find_next('p')
            summary = summary_tag.get_text(strip=True) if summary_tag else ""

            # Find published (next <p> after summary)
            published_tag = summary_tag.find_next('p') if summary_tag else None
            published = published_tag.get_text(strip=True) if published_tag else ""

            # Find URL if <a> is a parent or sibling
            a_tag = tag.find_parent('a') or tag.find_next('a')
            url = urljoin(url, a_tag['href']) if a_tag and a_tag.get('href') else ""

            headlines.append({
                "title": title,
                "summary": summary,
                "url": url,
                "published": published,
                "published_iso": parse_hebrew_time(published),      #raw
                "source": "channel14",
                "scraped_at": datetime.now().isoformat()
            })

    os.makedirs("data/raw", exist_ok=True)

    filename = f"data/raw/c14_scraped_{datetime.now().date()}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(headlines, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(headlines)} headlines to {filename}")






    # for debugging - 

    # for tag in soup.find_all(['time']):  #'h1', 'h2', 'h3', 'a', 'p', 'span', 
    #     print(tag.prettify())
    

    # with open("debug_tags.txt", "w", encoding="utf-8") as f:
    #     for tag in soup.find_all(['h1', 'h2', 'h3', 'a', 'p', 'span', 'time']):
    #         text = tag.get_text(strip=True)
    #         if text:
    #             f.write(f"<{tag.name}>: {text}\n")





    # @@Those are kinda good
    # headlines = []

    # for tag in soup.find_all(['h1', 'h2']):
    #     title = tag.get_text(strip=True)

    #     summary_tag = tag.find_next('p')
    #     summary = summary_tag.get_text(strip=True) if summary_tag else ""

    #     published_tag = summary_tag.find_next('p') if summary_tag else None
    #     published = published_tag.get_text(strip=True) if published_tag else ""

    #     headlines.append({
    #         "title": title,
    #         "summary": summary,
    #         "published": published,
    #         "source": "channel14",
    #         "scraped_at": datetime.now().isoformat()
    #     })