import json
import subprocess
from datetime import date

import config
from fetcher import fetch_news
from analyzer import (
    extract_keywords, sector_split, rank_articles, top_keywords_recent,
    party_exposure, city_exposure, time_split,
)
from reporter import generate_html
from security import sanitize


def _git_push(message: str) -> None:
    for cmd in (
        ["git", "add", "index.html"],
        ["git", "commit", "-m", message],
        ["git", "push"],
    ):
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[git] {' '.join(cmd)} failed:\n{result.stderr.strip()}")
            return


def run() -> None:
    print("Fetching Google News RSS ...")
    raw   = fetch_news(config.QUERIES)
    clean = sanitize(raw)

    # ── dual time-horizon split ───────────────────────────────────────────────
    h1, h12 = time_split(clean)

    # per-horizon sector splits
    pol_1h,  fin_1h  = sector_split(h1)
    pol_12h, fin_12h = sector_split(h12)

    # per-horizon rankings / keywords
    top5_1h  = rank_articles(h1,  top_n=5)
    top5_12h = rank_articles(h12, top_n=5)
    top_kw   = top_keywords_recent(clean, top_n=5)
    all_kw   = extract_keywords(clean, top_n=20)

    # per-horizon party / city exposure
    p_1h  = party_exposure(h1)
    p_12h = party_exposure(h12)
    c_1h  = city_exposure(h1)
    c_12h = city_exposure(h12)

    report = {
        "date":     str(date.today()),
        "sources":  {"google_news": len(raw), "h1": len(h1), "h12": len(h12)},
        "keywords": [[w, c] for w, c in all_kw],
    }

    with open(config.REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    generate_html(
        report,
        pol_1h, fin_1h, pol_12h, fin_12h,
        top5_1h, top5_12h,
        top_kw, all_kw,
        p_1h, p_12h, c_1h, c_12h,
        config.HTML_REPORT_PATH,
    )

    print(f"Saved -> {config.REPORT_PATH}  {config.HTML_REPORT_PATH}")
    print(f"  Total:{len(raw)}  1H:{len(h1)}  12H:{len(h12)}")
    print(f"  Pol 1H:{len(pol_1h)} Fin 1H:{len(fin_1h)} | Pol 12H:{len(pol_12h)} Fin 12H:{len(fin_12h)}")

    _git_push(f"chore: daily report {report['date']}")


if __name__ == "__main__":
    run()
