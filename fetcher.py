import urllib.parse
import calendar
import time
import feedparser
import config

_RSS_BASE = "https://news.google.com/rss/search"


def _fetch_query(query: str) -> list[dict]:
    url = f"{_RSS_BASE}?" + urllib.parse.urlencode({
        "q":    query,
        "hl":   config.LANGUAGE_CODE,
        "gl":   "TW",
        "ceid": "TW:zh-Hant",
        "num":  "100",
    })
    feed = feedparser.parse(url)
    results = []
    for e in feed.entries:
        pt = e.get("published_parsed")
        ts = calendar.timegm(pt) if pt else time.time()
        results.append({
            "title":       e.get("title", ""),
            "description": e.get("summary", ""),
            "link":        e.get("link", "#"),
            "published":   ts,
        })
    return results


def fetch_news(queries: list[str]) -> list[dict]:
    seen, items = set(), []
    for q in queries:
        for item in _fetch_query(q):
            if item["link"] not in seen:
                seen.add(item["link"])
                items.append(item)
    return items
