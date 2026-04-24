from __future__ import annotations

from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

TAIPEI = ZoneInfo("Asia/Taipei")

MARKET_GROUPS = OrderedDict([
    (
        "Asia",
        (
            ("^TWII", "Taiwan"),
            ("^N225", "Japan"),
            ("^KS11", "Korea"),
            ("^HSI", "Hong Kong"),
        ),
    ),
    (
        "USA",
        (
            ("^GSPC", "S&P 500"),
            ("^IXIC", "Nasdaq"),
            ("^SOX", "PHLX Semiconductor"),
        ),
    ),
    (
        "Commodities",
        (
            ("GC=F", "Gold"),
            ("BZ=F", "Brent Oil"),
            ("CL=F", "WTI Oil"),
        ),
    ),
])


def _local_now() -> datetime:
    return datetime.now(timezone.utc).astimezone(TAIPEI)


def _blank_quote(symbol: str, name: str, group: str, message: str) -> dict:
    return {
        "symbol": symbol,
        "name": name,
        "group": group,
        "price": None,
        "change": None,
        "change_percent": None,
        "direction": "flat",
        "updated_at": _local_now().isoformat(),
        "timezone": "Asia/Taipei",
        "source": "fallback",
        "status": "unavailable",
        "message": message,
    }


def _fetch_quote(symbol: str, name: str, group: str) -> dict:
    try:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d", interval="1d", auto_adjust=False)
        if hist.empty:
            raise RuntimeError("empty history")

        last = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) > 1 else last
        price = float(last.get("Close", 0.0) or 0.0)
        prev_close = float(prev.get("Close", price) or price)
        change = round(price - prev_close, 2)
        change_percent = round((change / prev_close * 100) if prev_close else 0.0, 2)

        return {
            "symbol": symbol,
            "name": name,
            "group": group,
            "price": round(price, 2),
            "change": change,
            "change_percent": change_percent,
            "direction": "up" if change >= 0 else "down",
            "updated_at": _local_now().isoformat(),
            "timezone": "Asia/Taipei",
            "source": "yfinance",
            "status": "ok",
        }
    except Exception as exc:
        return _blank_quote(symbol, name, group, str(exc))


def _summarize_group(group: str, items: list[dict]) -> dict:
    active = sum(1 for item in items if item.get("status") == "ok")
    return {
        "label": group,
        "count": len(items),
        "active": active,
        "items": items,
    }


def fetch_global_market_summary() -> dict:
    tasks: list[tuple[str, str, str]] = []
    for group, rows in MARKET_GROUPS.items():
        for symbol, name in rows:
            tasks.append((symbol, name, group))

    results: dict[str, list[dict]] = {group: [] for group in MARKET_GROUPS}
    with ThreadPoolExecutor(max_workers=min(8, len(tasks) or 1)) as pool:
        futures = [pool.submit(_fetch_quote, symbol, name, group) for symbol, name, group in tasks]
        for future in futures:
            quote = future.result()
            results.setdefault(quote["group"], []).append(quote)

    return {
        "status": "ok",
        "timezone": "Asia/Taipei",
        "updated_at": _local_now().isoformat(),
        "groups": [_summarize_group(group, results.get(group, [])) for group in MARKET_GROUPS],
    }


def fetch_tw_index_summary() -> dict:
    for group in fetch_global_market_summary().get("groups", []):
        for item in group.get("items", []):
            if item.get("symbol") == "^TWII":
                return item
    return _blank_quote("^TWII", "Taiwan", "Asia", "TWII quote not available")