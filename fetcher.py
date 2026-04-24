import calendar
import json
import os
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.parse import parse_qs, unquote, urlsplit, urlunsplit

import feedparser
import config

from modules.calendar.intl_calendar import fetch_intl_calendar
from modules.calendar.tw_calendar import fetch_tw_earnings_calls
from modules.market.global_markets import fetch_global_market_summary

_RSS_BASE = "https://news.google.com/rss/search"
_WINDOW_DAYS = 7

_POLITICS_HINTS = (
    "政治", "政府", "立法院", "總統", "選舉", "民進黨", "國民黨", "政院", "內閣",
    "法案", "外交", "兩岸", "罷免", "公投", "修憲", "黨團", "議會", "市長",
)
_FINANCE_HINTS = (
    "金融", "股市", "經濟", "匯率", "央行", "投資", "台股", "半導體", "外資",
    "利率", "通膨", "殖利率", "財訊", "經濟日報", "工商時報", "個股", "營收",
)
_INTL_HINTS = (
    "美國", "川普", "Fed", "聯準會", "華爾街", "美股", "NASDAQ", "關稅", "貿易戰",
    "烏克蘭", "中東", "石油", "能源", "美元", "Biden", "Trump", "Musk",
)
_REALESTATE_HINTS = (
    "房價", "房市", "房貸", "實價登錄", "新青安", "限貸令", "重劃區", "預售屋",
    "囤房稅", "豪宅稅", "央行", "租屋", "土地", "建商", "都更", "危老",
)
_AI_HINTS = (
    "AI", "人工智慧", "生成式AI", "OpenAI", "ChatGPT", "NVIDIA", "輝達", "晶片",
    "半導體", "伺服器", "資料中心", "機器人", "雲端", "大模型", "算力", "GPU",
)

_QUERY_BANKS: dict[str, tuple[str, ...]] = {
    "politics": (
        "內閣 政策", "立法院 法案", "選舉 罷免", "兩岸 外交", "行政院 預算",
        "民進黨 國民黨", "地方政府 議會", "憲政 公投",
    ),
    "finance": (
        "台股", "半導體", "個股營收", "外資買超", "美股趨勢", "經濟日報",
        "財訊", "殖利率", "通膨", "聯準會", "AI 產業", "財報", "ETF",
    ),
    "international": (
        "美國 川普", "Fed 利率", "華爾街", "地緣政治", "烏克蘭", "中東",
        "關稅 貿易戰", "石油 能源", "美元 匯率", "NASDAQ 美股",
    ),
    "real_estate": (
        "新青安", "限貸令", "實價登錄", "重劃區", "房貸利率", "豪宅稅",
        "預售屋趨勢", "房價走勢", "央行", "囤房稅",
        "site:house.udn.com", "site:estate.ltn.com.tw", "site:mygonews.com",
    ),
    "ai": (
        "人工智慧", "生成式AI", "AI晶片", "NVIDIA", "OpenAI", "ChatGPT",
        "資料中心", "機器人", "雲端", "算力",
    ),
    "generic": (
        "新聞", "市場", "政策", "科技", "經濟", "國際",
    ),
}

_SOURCE_BANKS: dict[str, tuple[str, ...]] = {
    "politics": ("中央社", "聯合報", "自由時報", "風傳媒"),
    "finance": ("經濟日報", "工商時報", "財訊", "MoneyDJ", "鉅亨網", "Yahoo財經"),
    "international": ("Reuters", "AP", "BBC", "CNN", "Financial Times"),
    "real_estate": ("經濟日報", "工商時報", "好房網", "591", "地產天下"),
    "ai": ("NVIDIA", "OpenAI", "路透", "科技新報", "數位時代"),
    "generic": ("中央社", "Reuters", "AP"),
}

_FETCH_VARIANTS: dict[str, tuple[tuple[str, str, str], ...]] = {
    "politics": ((config.LANGUAGE_CODE, "TW", "TW:zh-Hant"),),
    "real_estate": ((config.LANGUAGE_CODE, "TW", "TW:zh-Hant"),),
    "finance": (
        (config.LANGUAGE_CODE, "TW", "TW:zh-Hant"),
        ("en-US", "US", "US:en"),
        ("zh-HK", "HK", "HK:zh-Hant"),
    ),
    "international": (
        (config.LANGUAGE_CODE, "TW", "TW:zh-Hant"),
        ("en-US", "US", "US:en"),
        ("en-GB", "GB", "GB:en"),
    ),
    "ai": (
        (config.LANGUAGE_CODE, "TW", "TW:zh-Hant"),
        ("en-US", "US", "US:en"),
    ),
    "generic": ((config.LANGUAGE_CODE, "TW", "TW:zh-Hant"),),
}

_TRACKING_PARAMS = {
    "oc", "ved", "fbclid", "gclid", "yclid", "ref", "ref_src", "src",
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "hl", "gl", "ceid",
}


def _normalize_query(query: str) -> str:
    return " ".join(query.split()).strip()


def _sector_for_query(query: str) -> str:
    text = _normalize_query(query)
    if any(token in text for token in _REALESTATE_HINTS):
        return "real_estate"
    if any(token in text for token in _INTL_HINTS):
        return "international"
    if any(token in text for token in _FINANCE_HINTS):
        return "finance"
    if any(token in text for token in _POLITICS_HINTS):
        return "politics"
    if any(token.lower() in text.lower() for token in _AI_HINTS):
        return "ai"
    return "generic"


def _expanded_queries(base_query: str) -> list[str]:
    sector = _sector_for_query(base_query)
    bank = _QUERY_BANKS.get(sector, _QUERY_BANKS["generic"])
    sources = _SOURCE_BANKS.get(sector, _SOURCE_BANKS["generic"])
    base = _normalize_query(base_query)
    expanded = []
    for term in bank:
        candidate = _normalize_query(f"{base} {term}")
        if candidate not in expanded:
            expanded.append(candidate)
    for source in sources:
        candidate = _normalize_query(f"{base} {source}")
        if candidate not in expanded:
            expanded.append(candidate)
    if sector in {"finance", "real_estate", "ai"}:
        combo_topics = bank
        combo_sources = sources
    elif sector == "international":
        combo_topics = bank[: min(6, len(bank))]
        combo_sources = sources[: min(4, len(sources))]
    else:
        combo_topics = bank[: min(5, len(bank))]
        combo_sources = sources[: min(3, len(sources))]
    for term in combo_topics:
        for source in combo_sources:
            candidate = _normalize_query(f"{base} {term} {source}")
            if candidate not in expanded:
                expanded.append(candidate)
    return expanded or [base]


def _canonical_url(raw_url: str) -> str:
    if not raw_url:
        return "#"
    parsed = urlsplit(raw_url)
    if parsed.netloc == "news.google.com":
        params = parse_qs(parsed.query)
        for key in ("url", "q", "u"):
            values = params.get(key)
            if values:
                candidate = unquote(values[0])
                if candidate.startswith(("http://", "https://")):
                    return _canonical_url(candidate)
    query_items = []
    for key, value in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True):
        if key.startswith("utm_") or key in _TRACKING_PARAMS:
            continue
        query_items.append((key, value))
    normalized_query = urllib.parse.urlencode(query_items, doseq=True)
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, normalized_query, ""))


def _fetch_query(query: str, hl: str, gl: str, ceid: str) -> list[dict]:
    search_query = _normalize_query(query)
    if "when:" not in search_query:
        search_query = f"{search_query} when:{_WINDOW_DAYS}d"
    url = f"{_RSS_BASE}?" + urllib.parse.urlencode({
        "q":    search_query,
        "hl":   hl,
        "gl":   gl,
        "ceid": ceid,
        "num":  "100",
    })
    results = []
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Accept-Language": hl,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            feed = feedparser.parse(response)
    except Exception:
        return results
    for e in getattr(feed, "entries", []):
        pt = e.get("published_parsed")
        ts = calendar.timegm(pt) if pt else time.time()
        link = _canonical_url(e.get("link", "#"))
        results.append({
            "title":       e.get("title", ""),
            "description": e.get("summary", ""),
            "link":        link,
            "published":   ts,
        })
    return results


def fetch_news(queries: list[str]) -> list[dict]:
    items_by_link: dict[str, dict] = {}
    hits_by_link: dict[str, set[str]] = {}
    for q in queries:
        sector = _sector_for_query(q)
        variants = _FETCH_VARIANTS.get(sector, _FETCH_VARIANTS["generic"])
        for expanded_query in _expanded_queries(q):
            for hl, gl, ceid in variants:
                for item in _fetch_query(expanded_query, hl, gl, ceid):
                    link = item["link"]
                    hits_by_link.setdefault(link, set()).add(expanded_query)
                    if link not in items_by_link:
                        items_by_link[link] = item
    items = []
    for link, item in items_by_link.items():
        enriched = dict(item)
        enriched["_query_hits"] = max(1, len(hits_by_link.get(link, set())))
        items.append(enriched)
    return sorted(items, key=lambda item: item.get("published", 0), reverse=True)


def fetch_market_summary() -> dict:
    summary = fetch_global_market_summary()
    summary.setdefault("timezone", "Asia/Taipei")
    return summary


def fetch_calendar_events() -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "timezone": "Asia/Taipei",
        "tw": fetch_tw_earnings_calls(days=7),
        "intl": fetch_intl_calendar(days=7),
    }


def _write_json(path: str, payload: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def fetch_dashboard_assets(queries: list[str]) -> dict:
    with ThreadPoolExecutor(max_workers=3) as pool:
        news_future = pool.submit(fetch_news, queries)
        market_future = pool.submit(fetch_market_summary)
        calendar_future = pool.submit(fetch_calendar_events)

        def _safe_result(future, fallback):
            try:
                return future.result()
            except Exception:
                return fallback

        news = _safe_result(news_future, [])
        market_summary = _safe_result(market_future, {"status": "unavailable", "groups": []})
        calendar_events = _safe_result(calendar_future, {"tw": [], "intl": []})

    _write_json("data/market_summary.json", market_summary)
    _write_json("data/calendar_events.json", calendar_events)

    return {
        "news": news,
        "market_summary": market_summary,
        "calendar_events": calendar_events,
    }
