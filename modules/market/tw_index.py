from __future__ import annotations

from modules.market.global_markets import (
    fetch_global_market_summary as _fetch_global_market_summary,
    fetch_tw_index_summary as _fetch_tw_index_summary,
)


def fetch_twii_yfinance() -> dict:
    return _fetch_tw_index_summary()


def fetch_tw_index_summary() -> dict:
    return _fetch_tw_index_summary()


def fetch_global_market_summary() -> dict:
    return _fetch_global_market_summary()