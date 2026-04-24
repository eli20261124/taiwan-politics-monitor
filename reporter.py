import re
import html as _html
from analyzer import (
    seo_keywords, stance, party_tag, intl_icon,
    extract_keywords as _ekw, rank_articles as _rank, party_exposure as _pe,
)

_URL_RE = re.compile(r'https?://\S+')

_CSS = """
  /* SF Pro font stack */
  body {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display",
                 "SF Pro Text", "Helvetica Neue", system-ui, sans-serif; }

  /* Glass card */
  .glass {
    background: rgba(31,41,55,0.6);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px; }

  /* Off-canvas overlay */
  .oc-overlay {
    position: fixed; inset: 0; background: rgba(0,0,0,0.75);
    z-index: 200; opacity: 0; pointer-events: none;
    transition: opacity 0.3s ease; }
  .oc-overlay.active { opacity: 1; pointer-events: all; }

  /* Off-canvas panel */
  .oc-panel {
    position: fixed; top: 0; right: -100%;
    width: min(540px, 100vw); height: 100vh; overflow-y: auto;
    background: rgba(10,15,28,0.97);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border-left: 1px solid rgba(255,255,255,0.08);
    z-index: 201; padding: 1.5rem;
    transition: right 0.38s cubic-bezier(0.32,0.72,0,1); }
  .oc-panel.active { right: 0; }

  /* News card */
  .news-card {
    background: rgba(31,41,55,0.55);
    backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px; padding: 1rem;
    display: flex; flex-direction: column; justify-content: space-between;
    gap: 0.75rem; transition: border-color 0.2s, background 0.2s; }
    .news-card { height: 100%; min-height: 220px; }
  .news-card:hover { border-color: rgba(96,165,250,0.35);
    background: rgba(31,41,55,0.8); }

    .section-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1rem;
        align-items: stretch; }

    .dashboard-rail {
        position: fixed; top: 1rem; right: 1rem; width: min(21rem, calc(100vw - 1.5rem));
        max-height: calc(100vh - 2rem); overflow-y: auto; z-index: 45; }
    .calendar-card {
        background: rgba(17,24,39,0.58);
        backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px);
        border: 1px solid rgba(255,255,255,0.08); border-radius: 18px;
        box-shadow: 0 18px 45px rgba(0,0,0,0.22); }
    .market-table td,
    .market-table th { font-variant-numeric: tabular-nums; }
    .calendar-item {
        display: flex; gap: 0.5rem; align-items: flex-start;
        padding: 0.55rem 0.65rem; border-radius: 12px;
        background: rgba(255,255,255,0.03); }
    .status-light { width: 0.5rem; height: 0.5rem; border-radius: 999px; margin-top: 0.35rem; }
    .status-high { background: #ef4444; box-shadow: 0 0 0 3px rgba(239,68,68,0.12); }
    .status-routine { background: #22c55e; box-shadow: 0 0 0 3px rgba(34,197,94,0.12); }

  /* Description clamped */
  .card-desc {
    display: -webkit-box; -webkit-line-clamp: 3;
    -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis; }

  /* CTA button */
  .cta-btn {
    display: inline-block; flex-shrink: 0;
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.02em;
    padding: 0.25rem 0.7rem; border-radius: 20px;
    background: rgba(37,99,235,0.85); color: #fff;
    text-decoration: none; white-space: nowrap;
    transition: background 0.2s; }
  .cta-btn:hover { background: rgba(59,130,246,0.95); }

  /* Sidebar trigger button */
  .sidebar-btn {
    display: inline-flex; align-items: center; gap: 0.45rem;
    font-size: 0.8rem; font-weight: 700; letter-spacing: 0.01em;
    padding: 0.55rem 1.2rem; border-radius: 22px;
    background: rgba(17,24,39,0.8);
    border: 1px solid rgba(255,255,255,0.12); color: #93c5fd;
    cursor: pointer; transition: background 0.2s, border-color 0.2s; }
  .sidebar-btn:hover {
    background: rgba(55,65,81,0.9); border-color: rgba(96,165,250,0.5); }

  /* Time-horizon badge on section header */
  .horizon-badge {
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.06em;
    padding: 0.2rem 0.6rem; border-radius: 8px;
    background: rgba(255,255,255,0.08); color: #9ca3af; }

  /* Mobile */
  @media (max-width: 480px) {
    .oc-panel    { width: 100vw; padding: 1rem; }
        .dashboard-rail { position: static; width: auto; max-height: none; }
    body         { padding: 0.75rem !important; }
    .card-title  { font-size: 0.88rem; line-height: 1.35; }
    h1           { font-size: 1.45rem !important; }
    .sidebar-btn { font-size: 0.72rem; padding: 0.4rem 0.85rem; } }
"""

_JS = """
function openSidebar(id) {
  document.getElementById('ov-' + id).classList.add('active');
  document.getElementById('sb-' + id).classList.add('active');
  document.body.style.overflow = 'hidden';
}
function closeSidebar(id) {
  document.getElementById('ov-' + id).classList.remove('active');
  document.getElementById('sb-' + id).classList.remove('active');
  document.body.style.overflow = '';
}
"""


def _stance_badge(article):
    icon, label = stance(article)
    color = {
        "\U0001f534": "bg-red-900/60 text-red-300",
        "\U0001f7e2": "bg-green-900/60 text-green-300",
        "\u26aa":     "bg-gray-700/60 text-gray-300",
    }.get(icon, "bg-gray-700/60 text-gray-300")
    return f'<span class="text-xs px-2 py-0.5 rounded-full {color}">{icon} {label}</span>'


def _party_badge(article):
    icon, label = party_tag(article)
    if not icon:
        return ""
    color = {
        "\U0001f9e8": "bg-red-950/70 text-red-300 animate-pulse",
        "\U0001f7e6": "bg-blue-950/70 text-blue-300",
        "\U0001f7e9": "bg-green-950/70 text-green-300",
        "\u2b1c":     "bg-gray-700/60 text-gray-300",
    }.get(icon, "bg-gray-800/60 text-gray-400")
    return f'<span class="text-xs px-2 py-0.5 rounded-full font-bold {color}">{icon} {label}</span>'


def _intl_badge(article):
    icon = intl_icon(article)
    label_map = {
        "\U0001f6e2\ufe0f": "Energy",
        "\U0001f3e6":       "Fed",
        "\U0001f1fa\U0001f1f8": "US/Global",
    }
    label = label_map.get(icon, "Global")
    return (f'<span class="text-xs px-2 py-0.5 rounded-full font-bold'
            f' bg-indigo-900/60 text-indigo-300">{icon} {label}</span>')


def _seo_tags(article):
    return " ".join(
        f'<span class="text-xs bg-gray-700/50 text-gray-400 px-2 py-0.5 rounded-full">'
        f'#{_html.escape(t)}</span>'
        for t in seo_keywords(article)
    )


def _news_card(article, is_intl=False):
    title  = _html.escape(article.get("title", ""))
    url    = _html.escape(article.get("link", "#"))
    raw    = _URL_RE.sub("", article.get("description", "")).strip()
    desc   = _html.escape(raw[:300])
    badge_left = _intl_badge(article) if is_intl else _party_badge(article)
    badges = " ".join(filter(None, [badge_left, _stance_badge(article)]))
    return (
        f'<div class="news-card">'
        f'<div class="flex flex-col gap-2">'
        f'<a href="{url}" target="_blank" rel="noopener noreferrer"'
        f' class="card-title text-white font-semibold text-sm leading-snug hover:text-blue-300 transition-colors">{title}</a>'
        f'<div class="flex items-center gap-2 flex-wrap">{badges}</div>'
        f'<p class="card-desc text-gray-400 text-xs leading-relaxed">{desc}</p>'
        f'</div>'
        f'<div class="flex items-center justify-between gap-2 pt-2 border-t border-white/5">'
        f'  <div class="flex gap-1 flex-wrap">{_seo_tags(article)}</div>'
        f'  <a href="{url}" target="_blank" rel="noopener noreferrer" class="cta-btn">\u95b1\u8b80\u5168\u6587 \u2192</a>'
        f'</div>'
        f'</div>'
    )


def _kw_pills(keywords):
    if not keywords:
        return '<p class="text-gray-500 text-sm">\u7121\u8cc7\u6599</p>'
    max_c = keywords[0][1]
    pills = []
    for w, c in keywords[:10]:
        pct = int(c / max_c * 100)
        pills.append(
            f'<div class="flex items-center gap-3">'
            f'<span class="text-yellow-300 font-bold w-20 text-right shrink-0 text-sm">{_html.escape(w)}</span>'
            f'<div class="flex-1 bg-gray-700/50 rounded-full h-1.5">'
            f'<div class="bg-yellow-400 h-1.5 rounded-full" style="width:{pct}%"></div></div>'
            f'<span class="text-gray-500 text-xs w-6 text-right">{c}</span></div>'
        )
    return "\n".join(pills)


def _market_value(value):
    if value is None:
        return "--"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def _market_row(item):
    price = _market_value(item.get("price"))
    change = item.get("change")
    pct = item.get("change_percent")
    if change is None:
        change_text = "--"
        pct_text = "--"
        change_cls = "text-gray-500"
    else:
        change_cls = "text-emerald-400" if change >= 0 else "text-rose-400"
        sign = "+" if change >= 0 else ""
        change_text = f"{sign}{change:,.2f}"
        pct_text = f"{sign}{pct:,.2f}%"
    return (
        f'<tr class="border-t border-white/6">'
        f'  <td class="py-2 pr-2 text-white">'
        f'    <div class="text-sm font-semibold leading-tight">{_html.escape(item.get("name", item.get("symbol", "")))}</div>'
        f'    <div class="text-[10px] uppercase tracking-[0.16em] text-gray-500 tabular-nums">{_html.escape(item.get("symbol", ""))}</div>'
        f'  </td>'
        f'  <td class="py-2 text-right text-white tabular-nums">{price}</td>'
        f'  <td class="py-2 text-right tabular-nums {change_cls}">{change_text}</td>'
        f'  <td class="py-2 text-right tabular-nums {change_cls}">{pct_text}</td>'
        f'</tr>'
    )


def _market_group_card(group):
    items = group.get("items", []) if isinstance(group, dict) else []
    if not items:
        body = '<div class="text-xs text-gray-500 py-3">No data available</div>'
    else:
        body = (
            '<table class="w-full text-xs market-table">'
            '<thead>'
            '<tr class="text-[10px] uppercase tracking-[0.18em] text-gray-500">'
            '<th class="pb-2 text-left font-semibold">Market</th>'
            '<th class="pb-2 text-right font-semibold">Price</th>'
            '<th class="pb-2 text-right font-semibold">Chg</th>'
            '<th class="pb-2 text-right font-semibold">%</th>'
            '</tr>'
            '</thead>'
            '<tbody>'
            + ''.join(_market_row(item) for item in items)
            + '</tbody></table>'
        )
    return (
        f'<section class="rounded-2xl border border-white/8 bg-black/20 backdrop-blur-xl p-4 shadow-lg">'
        f'  <div class="mb-3 flex items-center justify-between gap-2">'
        f'    <h3 class="text-xs font-black uppercase tracking-[0.22em] text-gray-300">{_html.escape(group.get("label", "Market"))}</h3>'
        f'    <span class="text-[10px] text-gray-500 tabular-nums">{group.get("active", 0)}/{group.get("count", 0)}</span>'
        f'  </div>'
        f'  {body}'
        f'</section>'
    )


def _market_sidebar(market, calendar_events):
    groups = market.get("groups", []) if isinstance(market, dict) else []
    market_cards = ''.join(_market_group_card(group) for group in groups) if groups else (
        '<section class="rounded-2xl border border-white/8 bg-black/20 backdrop-blur-xl p-4 shadow-lg">'
        '<div class="text-xs text-gray-500">Market data unavailable</div>'
        '</section>'
    )
    return (
        '<aside class="dashboard-rail">'
        '  <div class="space-y-4">'
        '    <div class="glass p-4 shadow-2xl">'
        '      <div class="mb-3 flex items-center justify-between gap-2">'
        '        <div>'
        '          <div class="text-[10px] uppercase tracking-[0.24em] text-gray-500">Global Markets</div>'
        '          <div class="text-sm font-black text-white">Apple Minimal Sidebar</div>'
        '        </div>'
        '        <div class="text-[10px] text-gray-500 tabular-nums">Live</div>'
        '      </div>'
        f'      <div class="flex flex-col gap-4">{market_cards}</div>'
        '    </div>'
        f'    {_calendar_sidebar(calendar_events)}'
        '  </div>'
        '</aside>'
    )


def _calendar_list(events, title):
    items = events or []
    rows = []
    for item in items[:8]:
        level = item.get("impact", "routine")
        light = "status-high" if level == "high" else "status-routine"
        rows.append(
            f'<div class="calendar-item">'
            f'  <span class="status-light {light}"></span>'
            f'  <div class="min-w-0 flex-1">'
            f'    <div class="text-[11px] text-gray-400">{_html.escape(item.get("date", ""))} { _html.escape(item.get("time", "")) }</div>'
            f'    <div class="text-sm text-white font-semibold leading-snug">{_html.escape(item.get("title", item.get("event_name", "")))}</div>'
            f'    <div class="text-[11px] text-gray-500">{_html.escape(item.get("country", item.get("market", "")))}</div>'
            f'  </div>'
            f'</div>'
        )
    body = "".join(rows) or '<div class="text-xs text-gray-500">No upcoming items</div>'
    return (
        f'<div class="calendar-card p-4 mb-3">'
        f'  <div class="text-xs font-bold text-gray-400 uppercase tracking-[0.18em] mb-3">{_html.escape(title)}</div>'
        f'  <div class="flex flex-col gap-2">{body}</div>'
        f'</div>'
    )


def _calendar_sidebar(calendar_events):
    if not calendar_events:
        return (
            '<section class="glass p-4">'
            '  <div class="text-sm font-black text-white mb-3">📅 Financial Calendar</div>'
            '  <div class="text-xs text-gray-500">No upcoming items</div>'
            '</section>'
        )
    return (
        '<section class="glass p-4">'
        '  <div class="text-sm font-black text-white mb-3">📅 Financial Calendar</div>'
        f'    {_calendar_list(calendar_events.get("tw", []), "Taiwan Earnings Calls")}'
        f'    {_calendar_list(calendar_events.get("intl", []), "International Macro")}'
        '</section>'
    )


def _party_counts_bar(counts):
    total = sum(counts.values()) or 1
    cfg = {
        "KMT":   ("\U0001f7e6", "bg-blue-500",  "text-blue-300"),
        "DPP":   ("\U0001f7e9", "bg-green-500", "text-green-300"),
        "TPP":   ("\u2b1c",     "bg-gray-400",  "text-gray-300"),
        "Cross": ("\U0001f9e8", "bg-red-500",   "text-red-300"),
    }
    parts = []
    for key, (icon, bg, txt) in cfg.items():
        n   = counts.get(key, 0)
        pct = int(n / total * 100)
        parts.append(
            f'<div class="flex items-center gap-2">'
            f'<span class="{txt} text-xs font-bold w-16 shrink-0">{icon} {key}</span>'
            f'<div class="flex-1 bg-gray-700/50 rounded-full h-1.5">'
            f'<div class="{bg} h-1.5 rounded-full transition-all" style="width:{pct}%"></div></div>'
            f'<span class="text-gray-500 text-xs w-6 text-right">{n}</span>'
            f'</div>'
        )
    return f'<div class="flex flex-col gap-1.5 mb-4">{"".join(parts)}</div>'


def _top5_stories(articles):
    if not articles:
        return '<p class="text-gray-500 text-sm">\u6b64\u6642\u6bb5\u66ab\u7121\u52d7\u614b</p>'
    rows = []
    for i, a in enumerate(articles, 1):
        title = _html.escape(a.get("title", ""))
        url   = _html.escape(a.get("link", "#"))
        icon, label = stance(a)
        seo   = " ".join("#" + t for t in seo_keywords(a))
        rows.append(
            f'<div class="flex items-start gap-3 py-3 border-b border-white/5 last:border-0">'
            f'<span class="text-xl font-black text-gray-700 w-7 shrink-0">#{i}</span>'
            f'<div class="flex flex-col gap-1 flex-1 min-w-0">'
            f'<a href="{url}" target="_blank" rel="noopener noreferrer"'
            f' class="text-white font-semibold text-sm hover:text-blue-300 transition-colors leading-snug">{title}</a>'
            f'<div class="flex items-center justify-between gap-2 flex-wrap">'
            f'<span class="text-xs text-gray-500">{icon} {label} \u00b7 {seo}</span>'
            f'<a href="{url}" target="_blank" rel="noopener noreferrer" class="cta-btn shrink-0">'
            f'\u67e5\u770b\u4f86\u6e90 \u2192</a>'
            f'</div>'
            f'</div></div>'
        )
    return "\n".join(rows)


def _offcanvas(sector_id, title, articles, is_intl=False, time_label="12H"):
    kw    = _ekw(articles, top_n=10)
    top5  = _rank(articles, top_n=5)
    p     = _pe(articles)
    cards = "\n".join(_news_card(a, is_intl=is_intl) for a in articles) if articles else (
        '<p class="text-gray-500 text-sm py-8 text-center">\u6b64\u6642\u6bb5\u66ab\u7121\u65b0\u805e</p>'
    )
    safe  = _html.escape(title)
    return (
        f'<div id="ov-{sector_id}" class="oc-overlay" onclick="closeSidebar(\'{sector_id}\')"></div>'
        f'<aside id="sb-{sector_id}" class="oc-panel" role="dialog" aria-modal="true">'
        f'<div class="flex items-center justify-between mb-5">'
        f'  <h2 class="text-base font-black text-white">'
        f'    \U0001f4c2 {safe}'
        f'    <span class="ml-2 text-xs font-semibold text-gray-400 bg-white/5'
        f'      px-2 py-0.5 rounded-lg">{time_label}</span>'
        f'  </h2>'
        f'  <button onclick="closeSidebar(\'{sector_id}\')"'
        f'    class="text-gray-400 hover:text-white text-2xl leading-none transition-colors"'
        f'    aria-label="\u95dc\u9589">&times;</button>'
        f'</div>'
        f'<div class="mb-4">'
        f'  <p class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">'
        f'\U0001f3f3 \u653f\u9ee8\u66dd\u5149</p>'
        f'  {_party_counts_bar(p)}'
        f'</div>'
        f'<div class="glass p-4 mb-4">'
        f'  <h3 class="text-xs font-bold text-yellow-400 uppercase tracking-wider mb-3">'
        f'\U0001f525 \u71b1\u9580\u95dc\u9375\u5b57</h3>'
        f'  <div class="flex flex-col gap-2">{_kw_pills(kw)}</div>'
        f'</div>'
        f'<div class="glass p-4 mb-4">'
        f'  <h3 class="text-xs font-bold text-blue-400 uppercase tracking-wider mb-3">'
        f'\U0001f3c6 \u6d41\u91cf\u6392\u884c</h3>'
        f'  {_top5_stories(top5)}'
        f'</div>'
        f'<p class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">'
        f'\U0001f4f0 \u5168\u90e8\u65b0\u805e ({len(articles)} \u7bc7)</p>'
        f'<div class="flex flex-col gap-3">{cards}</div>'
        f'</aside>'
    )


def _sector_block(sector_id, title, icon, color, articles_1h, articles_12h, p_1h, label="1H"):
    cards = "\n".join(_news_card(a) for a in articles_1h[:10]) if articles_1h else (
        '<p class="text-gray-500 col-span-full py-8 text-center">'
        '\u6b64\u6642\u6bb5\u66ab\u7121\u65b0\u805e</p>'
    )
    sidebar = _offcanvas(sector_id, f"{icon} {title}", articles_12h, time_label="12H")
    n = min(len(articles_1h), 10)
    return (
        f'<section class="mb-14">'
        f'<div class="flex flex-wrap items-center gap-3 mb-5">'
        f'  <h2 class="text-2xl font-black {color}">{_html.escape(icon)} {_html.escape(title)}</h2>'
        f'  <span class="horizon-badge">\u26a1 {_html.escape(label)}</span>'
        f'  <span class="text-xs text-gray-600">Top {n} \u7bc7</span>'
        f'</div>'
        f'{_party_counts_bar(p_1h)}'
        f'<div class="section-grid mb-6">{cards}</div>'
        f'<div class="flex justify-center pt-2">'
        f'  <button class="sidebar-btn" onclick="openSidebar(\'{sector_id}\')">'
        f'    \U0001f4c2 \u67e5\u770b\u904e\u53bb 12 \u5c0f\u6642\u5b8c\u6574\u56de\u9867'
        f'  </button>'
        f'</div>'
        f'{sidebar}'
        f'</section>'
    )


def _sector_block_intl(articles_12h):
    p_12h = _pe(articles_12h)
    cards = "\n".join(_news_card(a, is_intl=True) for a in articles_12h[:10]) if articles_12h else (
        '<p class="text-gray-500 col-span-full py-8 text-center">'
        '\u6b64\u6642\u6bb5\u66ab\u7121\u65b0\u805e</p>'
    )
    n = min(len(articles_12h), 10)
    return (
        f'<section class="mb-14">'
        f'<div class="flex flex-wrap items-center gap-3 mb-5">'
        f'  <h2 class="text-2xl font-black text-sky-400">\U0001f310 \u570b\u969b\u6230\u60c5</h2>'
        f'  <span class="horizon-badge">\U0001f4c2 12H</span>'
        f'  <span class="text-xs text-gray-600">Top {n} \u7bc7</span>'
        f'</div>'
        f'{_party_counts_bar(p_12h)}'
        f'<div class="section-grid">{cards}</div>'
        f'</section>'
    )


def _sector_block_re(articles_7d, articles_30d):
    p_7d  = _pe(articles_7d)
    cards = "\n".join(_news_card(a) for a in articles_7d[:10]) if articles_7d else (
        '<p class="text-gray-500 col-span-full py-8 text-center">'
        '\u6b64\u6642\u6bb5\u66ab\u7121\u65b0\u805e</p>'
    )
    sidebar = _offcanvas("re", "\U0001f3e0 \u53f0\u7063\u623f\u5e02", articles_30d, time_label="30D")
    n = min(len(articles_7d), 10)
    return (
        f'<section class="mb-14">'
        f'<div class="flex flex-wrap items-center gap-3 mb-5">'
        f'  <h2 class="text-2xl font-black text-orange-400">\U0001f3e0 \u53f0\u7063\u623f\u5e02</h2>'
        f'  <span class="horizon-badge">\U0001f4c6 7D</span>'
        f'  <span class="text-xs text-gray-600">Top {n} \u7bc7</span>'
        f'</div>'
        f'{_party_counts_bar(p_7d)}'
        f'<div class="section-grid mb-6">{cards}</div>'
        f'<div class="flex justify-center pt-2">'
        f'  <button class="sidebar-btn" onclick="openSidebar(\'re\')">'
        f'    \U0001f4c2 \u67e5\u770b\u904e\u53bb 30 \u5929\u623f\u5e02\u8d70\u52e2'
        f'  </button>'
        f'</div>'
        f'{sidebar}'
        f'</section>'
    )


def _mini_bar(data, palette):
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


def _kw_bar_chart(keywords):
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


def _insights_block(p_1h, p_12h, c_1h, c_12h):
    party_pal = ["bg-blue-500", "bg-green-500", "bg-gray-400", "bg-red-500"]
    city_pal  = ["bg-indigo-400", "bg-cyan-400", "bg-teal-400",
                 "bg-orange-400", "bg-yellow-400", "bg-pink-400"]

    def _section(p, c):
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
        f'<div class="glass p-6">'
        f'  <details open>'
        f'    <summary class="cursor-pointer text-sm font-bold text-yellow-400 select-none">\u26a1 Last 1 Hour Snapshot</summary>'
        f'    {_section(p_1h, c_1h)}'
        f'  </details>'
        f'  <hr class="border-gray-700 my-4">'
        f'  <details>'
        f'    <summary class="cursor-pointer text-sm font-bold text-blue-400 select-none">\U0001f4c2 View 12H Historical Trends</summary>'
        f'    {_section(p_12h, c_12h)}'
        f'  </details>'
        f'</div>'
        f'</section>'
    )


def _legend_block():
    return (
        f'<div class="glass px-5 py-3 mb-8'
        f' flex flex-wrap gap-x-6 gap-y-1 items-center">'
        f'<span class="text-xs font-bold text-gray-400 uppercase tracking-wide mr-2">\U0001f4d6 \u5716\u4f8b</span>'
        f'<span class="text-xs text-gray-300">\U0001f7e6 KMT \u570b\u6c11\u9ee8</span>'
        f'<span class="text-xs text-gray-300">\U0001f7e9 DPP \u6c11\u9032\u9ee8</span>'
        f'<span class="text-xs text-gray-300">\u2b1c TPP \u6c11\u773e\u9ee8</span>'
        f'<span class="text-xs text-red-400 font-bold">\U0001f9e8 \u653f\u9ee8\u653b\u9632</span>'
        f'<span class="text-xs text-indigo-300">\U0001f1fa\U0001f1f8 US/Global \u00b7 \U0001f6e2\ufe0f Energy \u00b7 \U0001f3e6 Fed</span>'
        f'<span class="text-xs text-gray-500">\U0001f534 Volatile \u00b7 \U0001f7e2 Stable \u00b7 \u26aa Neutral</span>'
        f'</div>'
    )


def _top5_bar(articles):
    return (
        f'<div class="glass">'
        f'<h2 class="text-lg font-black text-white mb-4">\U0001f525 Top 5 Stories</h2>'
        f'{_top5_stories(articles)}'
        f'</div>'
    )


def _kw_pill_card(keywords):
    return (
        f'<div class="glass">'
        f'<h2 class="text-lg font-black text-white mb-4">\U0001f511 Trending Keywords</h2>'
        f'<div class="flex flex-col gap-3">{_kw_pills(keywords)}</div>'
        f'</div>'
    )


def generate_html(
    report,
    pol_1h,  fin_1h,
    pol_12h, fin_12h,
    intl_12h,
    re_7d,   re_30d,
    top5_1h, top5_12h,
    top_kw,  all_kw,
    p_1h, p_12h, c_1h, c_12h,
    output_path="index.html",
):
    import datetime as _dt
    today   = report.get("date", str(_dt.date.today()))
    now_str = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    total   = report.get("sources", {}).get("google_news", 0)
    h1_n    = report.get("sources", {}).get("h1", 0)
    h12_n   = report.get("sources", {}).get("h12", 0)
    market  = report.get("market_summary", {})
    calendar_events = report.get("calendar_events", {})
    labels = report.get("window_labels", {})

    pol_p_1h = _pe(pol_1h)
    fin_p_1h = _pe(fin_1h)

    politics_block = _sector_block(
        "pol", "\u653f\u6cbb Politics", "\U0001f3db\ufe0f", "text-purple-400",
        pol_1h, pol_12h, pol_p_1h, labels.get("politics", "1H"),
    )
    finance_block = _sector_block(
        "fin", "\u8ca1\u7d93 Finance", "\U0001f4c8", "text-green-400",
        fin_1h, fin_12h, fin_p_1h, labels.get("finance", "1H"),
    )
    intl_block = _sector_block_intl(intl_12h)
    re_block   = _sector_block_re(re_7d, re_30d)

    insights_block = _insights_block(p_1h, p_12h, c_1h, c_12h)
    kw_chart       = _kw_bar_chart(all_kw)
    legend         = _legend_block()
    right_sidebar  = _market_sidebar(market, calendar_events)

    page = (
        '<!DOCTYPE html>\n'
        '<html lang="zh-TW" class="bg-gray-900 text-gray-100">\n'
        '<head>\n'
        '<meta charset="UTF-8"/>\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1"/>\n'
        f'<title>\u53f0\u7063\u653f\u7d93\u6230\u60c5\u5ba4 \u2014 {today}</title>\n'
        '<script src="https://cdn.tailwindcss.com"></script>\n'
        f'<style>{_CSS}</style>\n'
        '</head>\n'
        '<body class="min-h-screen p-6 max-w-7xl mx-auto lg:pr-[24rem]">\n'
        '<header class="mb-6">\n'
        '  <h1 class="text-4xl font-black text-yellow-400 tracking-tight">'
        '\U0001f3db\ufe0f \u53f0\u7063\u653f\u7d93\u6230\u60c5\u5ba4</h1>\n'
        f'  <p class="text-gray-400 mt-1 text-sm">Taiwan Finance &amp; Politics Intelligence'
        f' \u00b7 Last Updated: <span class="text-white font-mono">{now_str}</span>'
        f' \u00b7 {total} articles'
        f' \u00b7 <span class="text-yellow-500">\u26a1 1H: {h1_n}</span>'
        f' / <span class="text-blue-400">\U0001f4c2 12H: {h12_n}</span></p>\n'
        '</header>\n'
        f'{right_sidebar}\n'
        f'{legend}\n'
        '<div class="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">\n'
        f'  <div class="lg:col-span-2">{_top5_bar(top5_1h)}</div>\n'
        f'  <div>{_kw_pill_card(top_kw)}</div>\n'
        '</div>\n'
        f'{politics_block}\n'
        f'{finance_block}\n'
        f'{intl_block}\n'
        f'{re_block}\n'
        f'{insights_block}\n'
        '<section class="mb-12">\n'
        '  <h2 class="text-xl font-bold text-white mb-4">\U0001f4ca Keyword Frequency</h2>\n'
        f'  <div class="glass p-6">{kw_chart}</div>\n'
        '</section>\n'
        f'<footer class="mt-10 text-gray-600 text-xs text-center">'
        f'\u53f0\u7063\u653f\u7d93\u6230\u60c5\u5ba4 \u00b7 Generated {now_str}</footer>\n'
        f'<script>{_JS}</script>\n'
        '</body>\n</html>'
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(page)
