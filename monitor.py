import json
import subprocess
from datetime import date

import config
from fetcher import fetch_dashboard_assets
from analyzer import (
    extract_keywords, sector_split, rank_articles, top_keywords_recent,
    party_exposure, city_exposure, time_split, time_split_buffered, time_split_re,
    time_window,
)
from reporter import generate_html
from security import sanitize


def _git_push(message: str) -> None:
    for cmd in (
        ["git", "add", "index.html", "README.md"],
        ["git", "commit", "-m", message],
        ["git", "push"],
    ):
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[git] {' '.join(cmd)} failed:\n{result.stderr.strip()}")
            return


def run() -> None:
    print("Fetching Google News RSS ...")
    assets = fetch_dashboard_assets(config.QUERIES)
    raw   = assets["news"]
    clean = sanitize(raw)

    # ── Standard sector split and adaptive hot windows ───────────────────────
    pol_all, fin_all, intl_all, re_all = sector_split(clean)
    pol_1h,  pol_12h,  pol_label  = time_split_buffered(pol_all)
    fin_1h,  fin_12h,  fin_label  = time_split_buffered(fin_all)
    intl_12h = time_window(intl_all, 12)

    # ── Real Estate: wider 7-day / 30-day horizons from the full pool ───────
    re_7d, re_30d = time_split_re(re_all)

    # ── Global rankings / keywords ────────────────────────────────────────────
    h1 = pol_1h + fin_1h + intl_12h
    h12 = pol_12h + fin_12h + intl_12h
    top5_1h  = rank_articles(h1,  top_n=5)
    top5_12h = rank_articles(h12, top_n=5)
    top_kw   = top_keywords_recent(clean, top_n=5)
    all_kw   = extract_keywords(clean, top_n=20)

    # ── Whole-horizon party / city exposure ───────────────────────────────────
    p_1h  = party_exposure(h1)
    p_12h = party_exposure(h12)
    c_1h  = city_exposure(h1)
    c_12h = city_exposure(h12)

    report = {
        "date":    str(date.today()),
        "sources": {
            "google_news": len(raw), "h1": len(h1), "h12": len(h12),
            "pol_1h": len(pol_1h), "fin_1h": len(fin_1h),
            "intl_12h": len(intl_12h),
            "re_7d": len(re_7d), "re_30d": len(re_30d),
        },
        "keywords": [[w, c] for w, c in all_kw],
        "market_summary": assets["market_summary"],
        "calendar_events": assets["calendar_events"],
        "window_labels": {
            "politics": pol_label,
            "finance": fin_label,
            "real_estate_primary": "房地產 (7D)",
            "real_estate_sidebar": "房地產 (30D)",
        },
    }

    with open(config.REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    generate_html(
        report,
        pol_1h,  fin_1h,
        pol_12h, fin_12h,
        intl_12h,
        re_7d, re_30d,
        top5_1h, top5_12h,
        top_kw, all_kw,
        p_1h, p_12h, c_1h, c_12h,
        config.HTML_REPORT_PATH,
    )

    print(f"Saved -> {config.REPORT_PATH}  {config.HTML_REPORT_PATH}")
    print(f"  Total:{len(raw)}  1H:{len(h1)}  12H:{len(h12)}")
    print(
        f"  Pol:{len(pol_1h)} Fin:{len(fin_1h)} (1H)"
        f"  |  Intl:{len(intl_12h)} (12H)"
        f"  |  RE 7D:{len(re_7d)} 30D:{len(re_30d)}"
    )

    _git_push(f"chore: daily report {report['date']}")


if __name__ == "__main__":
    run()
