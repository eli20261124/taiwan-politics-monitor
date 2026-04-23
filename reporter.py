import re
import html as _html
from datetime import date
from analyzer import seo_keywords, stance, party_tag

# Strip raw http(s) URLs that Google News sometimes injects into RSS summaries
_URL_RE = re.compile(r'https?://\S+')

# ── CSS injected into <head> ──────────────────────────────────────────────────
_TAB_CSS = """
  /* hide radio inputs but keep them functional */
  input.tab-radio { position:absolute; opacity:0; width:0; height:0; }
  /* hide all panels by default */
  .tab-panel { display:none; }
  /* Politics sector */
  #pol-1h:checked  ~ .pol-tabs label[for="pol-1h"],
  #pol-12h:checked ~ .pol-tabs label[for="pol-12h"] {
    background:#1f2937; color:#facc15; }
  #pol-1h:checked  ~ #pol-panel-1h  { display:block; }
  #pol-12h:checked ~ #pol-panel-12h { display:block; }
  /* Finance sector */
  #fin-1h:checked  ~ .fin-tabs label[for="fin-1h"],
  #fin-12h:checked ~ .fin-tabs label[for="fin-12h"] {
    background:#1f2937; color:#facc15; }
  #fin-1h:checked  ~ #fin-panel-1h  { display:block; }
  #fin-12h:checked ~ #fin-panel-12h { display:block; }
  /* Tab label base style */
  .tab-label {
    cursor:pointer; padding:0.35rem 1rem; border-radius:0.5rem;
    font-size:0.8rem; font-weight:600; color:#9ca3af;
    transition:background 0.2s, color 0.2s; white-space:nowrap; }
  /* Description clamped to 3 lines — prevents cards from stretching unevenly */
  .card-desc {
    display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical;
    overflow:hidden; text-overflow:ellipsis; }
  /* Mobile-first tweaks (iPhone 12 Mini = 375px wide) */
  @media (max-width:768px) {
    body        { padding:0.75rem !important; }
    .card-title { font-size:0.95rem; line-height:1.35; }
    .card-badges{ gap:0.25rem; }
    .cta-btn    { padding:0.2rem 0.6rem; font-size:0.7rem; }
    .tab-label  { padding:0.25rem 0.55rem; font-size:0.72rem; }
    h1          { font-size:1.6rem !important; } }
"""


def _stance_badge(article: dict) -> str:
    icon, label = stance(article)
    color = {
        "\U0001f534": "bg-red-900 text-red-300",
        "\U0001f7e2": "bg-green-900 text-green-300",
        "\u26aa":     "bg-gray-700 text-gray-300",
    }.get(icon, "bg-gray-700 text-gray-300")
    return f'<span class="text-xs px-2 py-0.5 rounded {color}">{icon} {label}</span>'


def _party_badge(article: dict) -> str:
    icon, label = party_tag(article)
    if not icon:
        return ""
    color = {
        "\U0001f9e8": "bg-red-950 text-red-300 animate-pulse",
        "\U0001f7e6": "bg-blue-950 text-blue-300",
        "\U0001f7e9": "bg-green-950 text-green-300",
        "\u2b1c":     "bg-gray-700 text-gray-300",
    }.get(icon, "bg-gray-800 text-gray-400")
    return f'<span class="text-xs px-2 py-0.5 rounded font-bold {color}">{icon} {label}</span>'


def _seo_tags(article: dict) -> str:
    return " ".join(
        f'<span class="text-xs bg-gray-700 text-gray-400 px-2 py-0.5 rounded">#{_html.escape(t)}</span>'
        for t in seo_keywords(article)
    )


def _news_card(article: dict) -> str:
    title  = _html.escape(article.get("title", ""))
    url    = _html.escape(article.get("link", "#"))
    # Strip raw URLs from description so none appear as visible text
    raw    = _URL_RE.sub("", article.get("description", "")).strip()
    desc   = _html.escape(raw[:300])
    badges = " ".join(filter(None, [_party_badge(article), _stance_badge(article)]))
    return (
        # flex-col + justify-between = equal height for all cards in a row
        f'<div class="bg-gray-800 rounded-xl p-4 border border-gray-700'
        f' flex flex-col justify-between gap-3">'

        # ── TOP section: title → badges → description ────────────────────
        f'<div class="flex flex-col gap-2">'
        # 1. Title — bold, large; the whole title is the clickable anchor
        f'<a href="{url}" target="_blank" rel="noopener noreferrer"'
        f' class="card-title text-white font-bold text-base leading-snug'
        f' hover:text-blue-300 transition-colors">{title}</a>'
        # 2. Party flag + stance badges
        f'<div class="card-badges flex items-center gap-2 flex-wrap">{badges}</div>'
        # 3. Summary — CSS-clamped 3 lines, no raw URLs
        f'<p class="card-desc text-gray-400 text-sm">{desc}</p>'
        f'</div>'

        # ── BOTTOM section: SEO tags + CTA button ────────────────────────
        f'<div class="flex items-center justify-between gap-2 pt-2 border-t border-gray-700">'
        f'  <div class="flex gap-1 flex-wrap">{_seo_tags(article)}</div>'
        f'  <a href="{url}" target="_blank" rel="noopener noreferrer"'
        f'     class="cta-btn shrink-0 text-xs font-semibold px-3 py-1 rounded-lg'
        f' bg-blue-600 hover:bg-blue-500 text-white transition-colors whitespace-nowrap">'
        f'    \u95b1\u8b80\u5168\u6587 \u2192</a>'
        f'</div>'

        f'</div>'
    )


def _party_counts_bar(counts: dict) -> str:
    total = sum(counts.values()) or 1
    parts = []
    cfg = {
        "KMT":   ("\U0001f7e6", "bg-blue-500",  "text-blue-300"),
        "DPP":   ("\U0001f7e9", "bg-green-500", "text-green-300"),
        "TPP":   ("\u2b1c",     "bg-gray-400",  "text-gray-300"),
        "Cross": ("\U0001f9e8", "bg-red-500",   "text-red-300"),
    }
    for key, (icon, bg, txt) in cfg.items():
        n   = counts.get(key, 0)
        pct = int(n / total * 100)
        parts.append(
            f'<div class="flex items-center gap-2">'
            f'<span class="{txt} text-sm font-bold w-16 shrink-0">{icon} {key}</span>'
            f'<div class="flex-1 bg-gray-700 rounded-full h-2">'
            f'<div class="{bg} h-2 rounded-full transition-all" style="width:{pct}%"></div></div>'
            f'<span class="text-gray-500 text-xs w-6 text-right">{n}</span>'
            f'</div>'
        )
    return f'<div class="flex flex-col gap-2 mb-4">{"".join(parts)}</div>'


def _mini_bar(data: dict, palette: list[str]) -> str:
    total = sum(data.values()) or 1
    bars  = []
    for i, (label, val) in enumerate(data.items()):
        h   = max(4, int(val / total * 80))
        col = palette[i % len(palette)]
        bars.append(
            f'<div class="flex flex-col items-center gap-1">'
            f'<span class="text-gray-400 text-xs">{val}</span>'
            f'<div class="{col} rounded-t w-8 transition-all" style="height:{h}px"></div>'
            f'<span class="text-gray-400 text-xs">{_html.escape(label)}</span>'
            f'</div>'
        )
    return f'<div class="flex items-end gap-3 overflow-x-auto pb-1">{"".join(bars)}</div>'


def _top5_stories(articles: list[dict]) -> str:
    if not articles:
        return '<p class="text-gray-500 text-sm">\u6b64\u6642\u6bb5\u66ab\u7121\u52d7\u614b</p>'
    rows = []
    for i, a in enumerate(articles, 1):
        title = _html.escape(a.get("title", ""))
        url   = _html.escape(a.get("link", "#"))
        icon, label = stance(a)
        seo   = " ".join("#" + t for t in seo_keywords(a))
        rows.append(
            f'<div class="flex items-start gap-3 py-3 border-b border-gray-700 last:border-0">'
            f'<span class="text-2xl font-black text-gray-600 w-8 shrink-0">#{i}</span>'
            f'<div class="flex flex-col gap-1 flex-1 min-w-0">'
            f'<a href="{url}" target="_blank" rel="noopener noreferrer"'
            f' class="text-white font-semibold hover:text-blue-300 transition-colors'
            f' leading-snug">{title}</a>'
            f'<div class="flex items-center justify-between gap-2 flex-wrap">'
            f'<span class="text-xs text-gray-500">{icon} {label} \u00b7 {seo}</span>'
            f'<a href="{url}" target="_blank" rel="noopener noreferrer"'
            f' class="cta-btn shrink-0 text-xs font-semibold px-2 py-0.5 rounded'
            f' bg-gray-700 hover:bg-gray-600 text-gray-300 transition-colors whitespace-nowrap">'
            f'\u67e5\u770b\u4f86\u6e90 \u2192</a>'
            f'</div>'
            f'</div></div>'
        )
    return "\n".join(rows)


def _kw_pills(keywords: list[tuple[str, int]]) -> str:
    if not keywords:
        return '<p class="text-gray-500 text-sm">\u7121\u8cc7\u6599</p>'
    max_c = keywords[0][1]
    pills = []
    for w, c in keywords[:10]:
        pct = int(c / max_c * 100)
        pills.append(
            f'<div class="flex items-center gap-3">'
            f'<span class="text-yellow-300 font-bold w-20 text-right shrink-0 text-sm">{_html.escape(w)}</span>'
            f'<div class="flex-1 bg-gray-700 rounded-full h-2">'
            f'<div class="bg-yellow-400 h-2 rounded-full" style="width:{pct}%"></div></div>'
            f'<span class="text-gray-500 text-xs w-6 text-right">{c}</span></div>'
        )
    return "\n".join(pills)


def _horizon_panel(panel_id: str, articles: list[dict],
                   top5: list[dict], kw: list[tuple[str, int]],
                   p_counts: dict) -> str:
    if not articles:
        cards_html = '<p class="text-gray-500 col-span-full py-8 text-center">\u6b64\u6642\u6bb5\u66ab\u7121\u65b0\u805e</p>'
    else:
        cards_html = "\n".join(_news_card(a) for a in articles[:10])
    return (
        f'<div id="{panel_id}" class="tab-panel">'
        f'{_party_counts_bar(p_counts)}'
        f'<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">'
        f'{cards_html}</div>'
        f'<div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">'
        f'  <div class="bg-gray-800 rounded-xl p-4 border border-gray-700">'
        f'    <h3 class="text-sm font-bold text-yellow-400 mb-3">\U0001f525 \u71b1\u9580\u95dc\u9375\u5b57</h3>'
        f'    <div class="flex flex-col gap-2">{_kw_pills(kw)}</div>'
        f'  </div>'
        f'  <div class="bg-gray-800 rounded-xl p-4 border border-gray-700">'
        f'    <h3 class="text-sm font-bold text-blue-400 mb-3">\U0001f3c6 \u6d41\u91cf\u6392\u884c</h3>'
        f'    {_top5_stories(top5)}'
        f'  </div>'
        f'</div>'
        f'</div>'
    )


def _sector_block(
    sector_id: str,
    title: str,
    icon: str,
    color: str,
    articles_1h:  list[dict], articles_12h: list[dict],
    top5_1h:      list[dict], top5_12h:     list[dict],
    kw_1h:  list[tuple[str, int]], kw_12h:  list[tuple[str, int]],
    p_1h:   dict,              p_12h:   dict,
) -> str:
    panel_1h  = f"{sector_id}-panel-1h"
    panel_12h = f"{sector_id}-panel-12h"
    tabs_cls  = f"{sector_id}-tabs"
    inp_1h    = f"{sector_id}-1h"
    inp_12h   = f"{sector_id}-12h"

    panel_1h_html  = _horizon_panel(panel_1h,  articles_1h,  top5_1h,  kw_1h,  p_1h)
    panel_12h_html = _horizon_panel(panel_12h, articles_12h, top5_12h, kw_12h, p_12h)

    return (
        f'<section class="mb-14 relative">'
        f'<input type="radio" id="{inp_1h}"  name="{sector_id}-horizon" class="tab-radio" checked>'
        f'<input type="radio" id="{inp_12h}" name="{sector_id}-horizon" class="tab-radio">'
        f'<div class="flex flex-wrap items-center justify-between gap-3 mb-5">'
        f'  <h2 class="text-2xl font-black {color}">{icon} {title}</h2>'
        f'  <div class="{tabs_cls} flex bg-gray-800 border border-gray-700 rounded-lg p-1 gap-1">'
        f'    <label for="{inp_1h}"  class="tab-label">\u26a1 \u8fd11\u5c0f\u6642</label>'
        f'    <label for="{inp_12h}" class="tab-label">\U0001f4c2 \u8fd112\u5c0f\u6642</label>'
        f'  </div>'
        f'</div>'
        f'{panel_1h_html}'
        f'{panel_12h_html}'
        f'</section>'
    )


def _kw_bar_chart(keywords: list[tuple[str, int]]) -> str:
    if not keywords:
        return ""
    max_c = keywords[0][1]
    bars  = []
    for w, c in keywords[:20]:
        h = max(4, int(c / max_c * 160))
        bars.append(
            f'<div class="flex flex-col items-center gap-1">'
            f'<span class="text-gray-400 text-xs">{c}</span>'
            f'<div class="bg-yellow-400 rounded-t w-8" style="height:{h}px"></div>'
            f'<span class="text-gray-400 text-xs">{_html.escape(w)}</span>'
            f'</div>'
        )
    return f'<div class="flex items-end gap-2 overflow-x-auto pb-2">{"".join(bars)}</div>'


def _insights_block(p_1h: dict, p_12h: dict, c_1h: dict, c_12h: dict) -> str:
    party_pal = ["bg-blue-500", "bg-green-500", "bg-gray-400", "bg-red-500"]
    city_pal  = ["bg-indigo-400", "bg-cyan-400", "bg-teal-400",
                 "bg-orange-400", "bg-yellow-400", "bg-pink-400"]

    def _section(p: dict, c: dict) -> str:
        return (
            f'<div class="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">'
            f'  <div>'
            f'    <h4 class="text-xs font-bold text-gray-400 uppercase mb-3">\U0001f3f3 \u653f\u9ee8\u66dd\u5149</h4>'
            f'    {_mini_bar(p, party_pal)}'
            f'  </div>'
            f'  <div>'
            f'    <h4 class="text-xs font-bold text-gray-400 uppercase mb-3">\U0001f3d9 \u57ce\u5e02\u5206\u4f48</h4>'
            f'    {_mini_bar(c, city_pal)}'
            f'  </div>'
            f'</div>'
        )

    return (
        f'<section class="mb-12">'
        f'<h2 class="text-xl font-bold text-white mb-4">\U0001f4ca Data Insights \u2014 \u653f\u9ee8\u8207\u57ce\u5e02\u66dd\u5149</h2>'
        f'<div class="bg-gray-800 rounded-xl p-6 border border-gray-700">'
        f'  <details open>'
        f'    <summary class="cursor-pointer text-sm font-bold text-yellow-400 select-none">'
        f'      \u26a1 Last 1 Hour Snapshot</summary>'
        f'    {_section(p_1h, c_1h)}'
        f'  </details>'
        f'  <hr class="border-gray-700 my-4">'
        f'  <details>'
        f'    <summary class="cursor-pointer text-sm font-bold text-blue-400 select-none">'
        f'      \U0001f4c2 View 12H Historical Trends</summary>'
        f'    {_section(p_12h, c_12h)}'
        f'  </details>'
        f'</div>'
        f'</section>'
    )


def _legend_block() -> str:
    """Compact always-visible legend explaining all icons and badges."""
    return (
        f'<div class="bg-gray-800 border border-gray-700 rounded-xl px-5 py-3 mb-8'
        f' flex flex-wrap gap-x-6 gap-y-1 items-center">'
        f'<span class="text-xs font-bold text-gray-400 uppercase tracking-wide mr-2">'
        f'\U0001f4d6 \u5716\u4f8b</span>'
        f'<span class="text-xs text-gray-300">\U0001f7e6 KMT \u570b\u6c11\u9ee8</span>'
        f'<span class="text-xs text-gray-300">\U0001f7e9 DPP \u6c11\u9032\u9ee8</span>'
        f'<span class="text-xs text-gray-300">\u2b1c TPP \u6c11\u773e\u9ee8</span>'
        f'<span class="text-xs text-gray-300">\U0001f534 \u5176\u4ed6/\u7121\u9ee8\u7c4d</span>'
        f'<span class="text-xs text-red-400 font-bold">'
        f'\U0001f9e8 \u653f\u9ee8\u653b\u9632 = \u5075\u6e2c\u5230\u591a\u9ee8\u6d3e\u95dc\u9375\u5b57</span>'
        f'<span class="text-xs text-gray-500">\U0001f534 Volatile'
        f' \u00b7 \U0001f7e2 Stable \u00b7 \u26aa Neutral</span>'
        f'</div>'
    )


def _top5_bar(articles: list[dict]) -> str:
    return (
        f'<div class="bg-gray-800 rounded-xl p-6 border border-gray-700">'
        f'<h2 class="text-xl font-bold text-white mb-4">\U0001f525 Top 5 Stories</h2>'
        f'{_top5_stories(articles)}'
        f'</div>'
    )


def _kw_pill_card(keywords: list[tuple[str, int]]) -> str:
    return (
        f'<div class="bg-gray-800 rounded-xl p-6 border border-gray-700">'
        f'<h2 class="text-xl font-bold text-white mb-4">\U0001f511 Trending Keywords</h2>'
        f'<div class="flex flex-col gap-3">{_kw_pills(keywords)}</div>'
        f'</div>'
    )


def generate_html(
    report: dict,
    pol_1h:  list[dict], fin_1h:  list[dict],
    pol_12h: list[dict], fin_12h: list[dict],
    top5_1h: list[dict], top5_12h: list[dict],
    top_kw:  list[tuple[str, int]],
    all_kw:  list[tuple[str, int]],
    p_1h:    dict, p_12h: dict,
    c_1h:    dict, c_12h: dict,
    output_path: str = "index.html",
) -> None:
    import datetime as _dt
    today   = report.get("date", str(_dt.date.today()))
    now_str = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    total   = report.get("sources", {}).get("google_news", 0)
    h1_n    = report.get("sources", {}).get("h1", 0)
    h12_n   = report.get("sources", {}).get("h12", 0)

    from analyzer import extract_keywords as _ekw, rank_articles as _rank, party_exposure as _pe
    pol_kw_1h  = _ekw(pol_1h,  top_n=10)
    fin_kw_1h  = _ekw(fin_1h,  top_n=10)
    pol_kw_12h = _ekw(pol_12h, top_n=10)
    fin_kw_12h = _ekw(fin_12h, top_n=10)

    pol_top5_1h  = _rank(pol_1h,  top_n=5)
    fin_top5_1h  = _rank(fin_1h,  top_n=5)
    pol_top5_12h = _rank(pol_12h, top_n=5)
    fin_top5_12h = _rank(fin_12h, top_n=5)

    pol_p_1h  = _pe(pol_1h);  pol_p_12h = _pe(pol_12h)
    fin_p_1h  = _pe(fin_1h);  fin_p_12h = _pe(fin_12h)

    politics_block = _sector_block(
        "pol", "\u653f\u6cbb Politics", "\U0001f3db\ufe0f", "text-purple-400",
        pol_1h, pol_12h, pol_top5_1h, pol_top5_12h,
        pol_kw_1h, pol_kw_12h, pol_p_1h, pol_p_12h,
    )
    finance_block = _sector_block(
        "fin", "\u8ca1\u7d93 Finance", "\U0001f4c8", "text-green-400",
        fin_1h, fin_12h, fin_top5_1h, fin_top5_12h,
        fin_kw_1h, fin_kw_12h, fin_p_1h, fin_p_12h,
    )
    insights_block = _insights_block(p_1h, p_12h, c_1h, c_12h)
    kw_chart       = _kw_bar_chart(all_kw)
    legend         = _legend_block()

    page = (
        '<!DOCTYPE html>\n'
        '<html lang="zh-TW" class="bg-gray-900 text-gray-100">\n'
        '<head>\n'
        '<meta charset="UTF-8"/>\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1"/>\n'
        f'<title>\u53f0\u7063\u653f\u7d93\u6230\u60c5\u5ba4 \u2014 {today}</title>\n'
        '<script src="https://cdn.tailwindcss.com"></script>\n'
        f'<style>{_TAB_CSS}</style>\n'
        '</head>\n'
        '<body class="min-h-screen p-6 max-w-7xl mx-auto">\n'

        '<header class="mb-6">\n'
        '  <h1 class="text-4xl font-black text-yellow-400 tracking-tight">'
        '\U0001f3db\ufe0f \u53f0\u7063\u653f\u7d93\u6230\u60c5\u5ba4</h1>\n'
        f'  <p class="text-gray-400 mt-1 text-sm">'
        f'Taiwan Finance &amp; Politics Intelligence'
        f' \u00b7 Last Updated: <span class="text-white font-mono">{now_str}</span>'
        f' \u00b7 {total} articles'
        f' \u00b7 <span class="text-yellow-500">\u26a1 1H: {h1_n}</span>'
        f' / <span class="text-blue-400">\U0001f4c2 12H: {h12_n}</span></p>\n'
        '</header>\n'

        f'{legend}\n'

        '<div class="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">\n'
        f'  <div class="lg:col-span-2">{_top5_bar(top5_1h)}</div>\n'
        f'  <div>{_kw_pill_card(top_kw)}</div>\n'
        '</div>\n'

        f'{politics_block}\n'
        f'{finance_block}\n'
        f'{insights_block}\n'

        '<section class="mb-12">\n'
        '  <h2 class="text-xl font-bold text-white mb-4">\U0001f4ca Keyword Frequency</h2>\n'
        f'  <div class="bg-gray-800 rounded-xl p-6 border border-gray-700">{kw_chart}</div>\n'
        '</section>\n'

        f'<footer class="mt-10 text-gray-600 text-xs text-center">'
        f'\u53f0\u7063\u653f\u7d93\u6230\u60c5\u5ba4 \u00b7 Generated {now_str}'
        f'</footer>\n'
        '</body>\n</html>'
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(page)
