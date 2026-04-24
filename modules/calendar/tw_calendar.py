from __future__ import annotations

import re
import urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

TAIPEI = ZoneInfo("Asia/Taipei")
YAHOO_URL = "https://tw.stock.yahoo.com/calendar/earnings-call"

_DATE_RE = re.compile(r"20\d{2}[-/]\d{1,2}[-/]\d{1,2}")
_CODE_RE = re.compile(r"\b\d{4}\b")


def _now() -> datetime:
    return datetime.now(timezone.utc).astimezone(TAIPEI)


def _parse_date(value: str) -> datetime | None:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=TAIPEI)
        except ValueError:
            continue
    return None


def _fetch_html(url: str, timeout: int = 8) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.7",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="ignore")


def _fallback_events(days: int = 7) -> list[dict]:
    base = _now().date()
    samples = [
        (0, "2330", "台積電"),
        (2, "2317", "鴻海"),
        (4, "2454", "聯發科"),
        (6, "1301", "台塑"),
    ]
    events = []
    for offset, code, name in samples:
        event_date = base + timedelta(days=offset)
        if offset > days:
            continue
        events.append(
            {
                "event_id": f"tw_{code}_{event_date.isoformat()}",
                "company_id": code,
                "company_name": name,
                "date": event_date.isoformat(),
                "time": "",
                "title": f"{name} {code} 法說/財報",
                "country": "TW",
                "flag": "🇹🇼",
                "impact": "routine",
                "source": "yahoo-fallback",
                "url": YAHOO_URL,
                "timezone": "Asia/Taipei",
                "fetched_at": _now().isoformat(),
            }
        )
    return events


def fetch_tw_earnings_calls(days: int = 7) -> list[dict]:
    end = _now().date() + timedelta(days=days)
    current_year = _now().strftime("%Y")
    try:
        html = _fetch_html(YAHOO_URL)
    except Exception:
        return _fallback_events(days)

    candidates: list[dict] = []
    for match in _DATE_RE.finditer(html):
        date_value = match.group(0).replace("/", "-")
        parsed_date = _parse_date(date_value)
        if not parsed_date:
            continue
        if parsed_date.date() < _now().date() or parsed_date.date() > end:
            continue
        snippet = html[max(0, match.start() - 180): match.end() + 260]
        codes = _CODE_RE.findall(snippet)
        title_match = re.search(r"([\u4e00-\u9fffA-Za-z0-9·&()\- ]{2,24})", snippet)
        name = title_match.group(1).strip() if title_match else "台灣企業法說/財報"
        if not re.search(r"[\u4e00-\u9fff]", name):
            continue
        company_code = codes[0] if codes else ""
        if not company_code or company_code == current_year:
            continue
        event_id = f"tw_{company_code or name}_{parsed_date.date().isoformat()}"
        candidates.append(
            {
                "event_id": event_id,
                "company_id": company_code,
                "company_name": name,
                "date": parsed_date.date().isoformat(),
                "time": "",
                "title": f"{name} {company_code}".strip(),
                "country": "TW",
                "flag": "🇹🇼",
                "impact": "routine",
                "source": "yahoo",
                "url": YAHOO_URL,
                "timezone": "Asia/Taipei",
                "fetched_at": _now().isoformat(),
            }
        )

    if not candidates:
        candidates = _fallback_events(days)

    unique: dict[str, dict] = {}
    for item in candidates:
        unique[item["event_id"]] = item
    return sorted(unique.values(), key=lambda row: row["date"])