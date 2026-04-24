import re
import html
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import jieba
from collections import Counter

_STOP = {
    "的","了","在","是","我","有","和","就","不","人","都","一","上",
    "也","很","到","說","要","去","你","會","著","看","好","自己","這",
    "他","她","它","我們","你們","他們","但","而","與","及","或","於",
    "台灣","記者","報導","新聞","表示","指出","相關","目前","已經",
}

_TAG_RE = re.compile(r"<[^>]+>")

_POLITICS_KW = {
    "政治","政府","選舉","立法院","總統","民進黨","國民黨","政策","外交","兩岸",
    "立委","行政院","內閣","罷免","修憲","公投","抗議","示威","爭議","法案",
    "政院","黨團","議會","地方政府","憲政","預算審查","監督","國會改革","國安",
}
_FINANCE_KW  = {
    "金融","股市","經濟","匯率","央行","投資","漲","跌","市場","利率",
    "通膨","貿易","出口","企業","財政","預算","上市","基金","債券","外資",
    "台股","個股","財報","營收","EPS","殖利率","ETF","期貨","選股","半導體",
    "電子股","權值股","法人","投信","自營商","外資買超","現金殖利率","資本支出",
    "獲利","盈餘","毛利率","財測","經濟日報","工商時報","財訊","MoneyDJ",
    "鉅亨網","Yahoo財經","台積電","聯發科","AI伺服器","資料中心","輝達","NVIDIA",
    "OpenAI","ChatGPT","生成式AI","雲端","AI晶片","機器學習","大數據","財經",
    "市場波動","融資","融券","基金淨值","公司治理",
}
_AI_KW = {
    "AI","人工智慧","生成式AI","OpenAI","ChatGPT","NVIDIA","輝達","AI晶片",
    "資料中心","伺服器","雲端","機器人","算力","GPU","大模型","LLM","深度學習",
}
_INTL_KW     = {"美國","川普","Trump","華爾街","特斯拉","Tesla","Fed","聯準會","拜登","Biden",
                "NASDAQ","那斯達克","石油","Oil","能源","Energy","利率升降","烏克蘭","中東",
                "關稅","貿易戰","美元","美股","道瓊","標普","馬斯克","Musk"}
_REALESTATE_KW = {
    "房價","實價登錄","預售屋","房貸","央行信用管制","容積率","租屋","買房",
    "建商","土地","房市","房屋","購屋","貸款","都市計畫","地段","重劃區",
    "地政","坪數","公設比","屋齡","凶宅","青安貸款","新青安","限貸令","囤房稅",
    "豪宅稅","實價登錄2.0","預售屋禁轉","房貸利率","房貸成數","首購","換屋",
    "中古屋","社區","建照","使照","推案","完銷","開工","交屋","土地開發","都更",
    "危老","租金","包租代管","打房","房價走勢","房市走勢","區域行情","蛋白區",
    "蛋黃區","捷運宅","學區宅","法拍","法拍屋","法拍市場","房貸寬限期","新案",
    "交易量","成屋","銷售率","建築貸款","信貸","銀行鑑價","土地銀行",
}

# Sub-sets for International smart icons (priority: Energy > Fed > US default)
_INTL_ENERGY_KW = {"石油","Oil","能源","Energy","烏克蘭","中東","天然氣","原油","OPEC"}
_INTL_FED_KW    = {"Fed","聯準會","利率升降","升息","降息","貨幣政策","美國央行","債券"}

_VOLATILE = {"跌","崩","危機","衝突","反對","抗議","罷工","戰爭","制裁","醜聞","彈劾","罷免","爭議","緊張"}
_STABLE   = {"漲","成長","穩定","合作","支持","通過","簽署","復甦","改善","突破","創新","升","獲利"}


def _clean(s: str) -> str:
    return _TAG_RE.sub(" ", html.unescape(s))


def _words(text: str) -> list[str]:
    return [w for w in jieba.cut(_clean(text)) if len(w) > 1 and w not in _STOP]


def _text_from(records: list[dict]) -> str:
    parts = []
    for r in records:
        parts += [_clean(r.get("title", "")), _clean(r.get("description", ""))]
    return " ".join(filter(None, parts))


def _published_dt(article: dict, now: Optional[datetime] = None) -> datetime:
    ts = article.get("published")
    if ts is None:
        return now or datetime.now(timezone.utc)
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def _article_age_hours(article: dict, now: datetime) -> float:
    age = now - _published_dt(article, now)
    return max(0.0, age.total_seconds() / 3600.0)


def extract_keywords(records: list[dict], top_n: int = 20) -> list[tuple[str, int]]:
    return Counter(_words(_text_from(records))).most_common(top_n)


def seo_keywords(article: dict) -> list[str]:
    text = article.get("title", "") + " " + article.get("description", "")
    return [w for w, _ in Counter(_words(text)).most_common(5)][:3]


def stance(article: dict) -> tuple[str, str]:
    text  = article.get("title", "") + article.get("description", "")
    words = set(jieba.cut(_clean(text)))
    v = len(words & _VOLATILE)
    s = len(words & _STABLE)
    if v > s:  return ("🔴", "Volatile")
    if s > v:  return ("🟢", "Stable")
    return ("⚪", "Neutral")


def intl_icon(article: dict) -> str:
    """Return the smart icon for an International-sector article."""
    text = article.get("title", "") + article.get("description", "")
    if any(k in text for k in _INTL_ENERGY_KW):
        return "\U0001f6e2\ufe0f"  # 🛢️
    if any(k in text for k in _INTL_FED_KW):
        return "\U0001f3e6"        # 🏦
    return "\U0001f1fa\U0001f1f8"  # 🇺🇸


def classify(article: dict) -> str:
    """4-way classifier: real_estate > international > finance > politics.

    Real Estate and International use direct substring matching (keywords are
    long, specific phrases — no jieba needed and avoids tokenization edge cases).
    Finance vs Politics uses jieba-intersection for shorter, ambiguous tokens.
    """
    text  = article.get("title", "") + article.get("description", "")
    # Real estate: ≥2 substring hits to avoid stray matches
    if sum(1 for k in _REALESTATE_KW if k in text) >= 2:
        return "real_estate"
    # International: any single keyword is sufficient
    if any(k in text for k in _INTL_KW):
        return "international"
    words = set(jieba.cut(_clean(text)))
    finance_terms = _FINANCE_KW | _AI_KW
    if len(words & finance_terms) >= len(words & _POLITICS_KW):
        return "finance"
    return "politics"


def sector_split(
    articles: list[dict],
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """Return (politics, finance, international, real_estate)."""
    politics, finance, international, real_estate = [], [], [], []
    for a in articles:
        cat = classify(a)
        if cat == "real_estate":   real_estate.append(a)
        elif cat == "international": international.append(a)
        elif cat == "finance":     finance.append(a)
        else:                      politics.append(a)
    return politics, finance, international, real_estate


def _window(articles: list[dict], hours: int) -> list[dict]:
    now = datetime.now(timezone.utc)
    return [a for a in articles if now - _published_dt(a, now) <= timedelta(hours=hours)]


def time_window(articles: list[dict], hours: int) -> list[dict]:
    return _window(articles, hours)


def time_split_buffered(articles: list[dict], minimum_count: int = 5) -> tuple[list[dict], list[dict], str]:
    primary = _window(articles, 1)
    if len(primary) < minimum_count:
        primary = _window(articles, 3)
        label = "熱點動態 (1H-3H)"
    else:
        label = "熱點動態 (1H)"
    sidebar = _window(articles, 12)
    return primary, (sidebar or articles), label


def _recency_score(article: dict, now: float) -> float:
    age_hours = max(0.0, (now - article.get("published", now)) / 3600.0)
    return 1.0 / ((age_hours + 1.0) ** 1.8)


def rank_articles(articles: list[dict], top_n: int = 5) -> list[dict]:
    now_dt   = datetime.now(timezone.utc)
    all_freq = Counter(_words(_text_from(articles)))
    scored   = []
    for a in articles:
        text_words = _words(a.get("title", "") + " " + a.get("description", ""))
        freq = sum(all_freq[w] for w in text_words)
        age_hours = _article_age_hours(a, now_dt)
        score = freq / ((age_hours + 1.0) ** 1.8)
        if age_hours < 0.75:
            score *= 1.5
        if a.get("_query_hits", 1) >= 3:
            score *= 1.2
        scored.append((score, a))
    scored.sort(key=lambda x: (x[0], x[1].get("published", 0)), reverse=True)
    return [a for _, a in scored[:top_n]]


def top_keywords_recent(articles: list[dict], top_n: int = 5) -> list[tuple[str, int]]:
    now    = time.time()
    recent = [a for a in articles if now - a.get("published", now) <= 3600] or articles
    return Counter(_words(_text_from(recent))).most_common(top_n)


_KMT = {"國民黨","藍營","朱立倫","侯友宜","蔣萬安","韓國瑜","盧秀燕","馬英九","趙少康",
        "徐巧芯","傅崐萁","洪孟楷","羅智強","凌濤","謝國樑","黨中央","八法案","藍白合",
        "國會改革","兩岸關係","九二共識","憲法法庭","罷免案","地方執政","黨團總召",
        "市政建設","兩岸和平","振興方案","軍購案","能源政策","核能"}

_DPP = {"民進黨","綠營","賴清德","蕭美琴","卓榮泰","鄭麗君","王定宇","吳思瑤","范雲",
        "莊瑞雄","林佳龍","顧立雄","沈伯洋","黃捷","黨部","執政黨","民主進步黨",
        "台灣主權","轉型正義","抗中保台","能源轉型","社會住宅","數位轉型","南向政策",
        "外交突破","認知作戰","國務青","經濟成果","韌性台灣","非核"}

_TPP = {"民眾黨","白營","柯文哲","黃國昌","黃珊珊","陳昭姿","張啟楷","林國成","麥玉珍",
        "吳春城","黨主席","關鍵少數","第三勢力","民眾之聲","小草","財政紀律","公開透明",
        "居住正義","國會調查權","兩岸一家親","五大案","三黨鼎立","聯合政府","柯粉",
        "戰狼","憲政改革","司法公正","能源務實","世代正義"}

_CITIES = ["台北", "新北", "桃園", "台中", "台南", "高雄"]


def party_tag(article: dict) -> tuple[str, str]:
    text    = article.get("title", "") + article.get("description", "")
    has_kmt = any(k in text for k in _KMT)
    has_dpp = any(k in text for k in _DPP)
    has_tpp = any(k in text for k in _TPP)
    n = sum([has_kmt, has_dpp, has_tpp])
    if n >= 2:   return ("🧨", "政黨攻防")
    if has_kmt:  return ("🟦", "KMT")
    if has_dpp:  return ("🟩", "DPP")
    if has_tpp:  return ("⬜", "TPP")
    return ("", "")


def party_exposure(articles: list[dict]) -> dict:
    counts = {"KMT": 0, "DPP": 0, "TPP": 0, "Cross": 0}
    for a in articles:
        _, label = party_tag(a)
        if label == "政黨攻防": counts["Cross"] += 1
        elif label in counts:   counts[label]   += 1
    return counts


def city_exposure(articles: list[dict]) -> dict:
    counts = {c: 0 for c in _CITIES}
    for a in articles:
        text = a.get("title", "") + a.get("description", "")
        for city in _CITIES:
            if city in text:
                counts[city] += 1
    return counts


def time_split(articles: list[dict]) -> tuple[list[dict], list[dict]]:
    """Return (h1, h12): articles from the last 1h and last 12h respectively.
    The 1H bucket is strict; only the 12H view retains a fallback.
    """
    now = datetime.now(timezone.utc)
    h1  = [a for a in articles if now - _published_dt(a, now) <= timedelta(hours=1)]
    h12 = [a for a in articles if now - _published_dt(a, now) <= timedelta(hours=12)]
    return h1, (h12 or articles)


def time_split_re(articles: list[dict]) -> tuple[list[dict], list[dict]]:
    """Return (d7, d30): Real Estate articles from last 7 days and 30 days.
    Falls back to most-recent 20 (d7) or all articles (d30) if window empty.
    """
    now = datetime.now(timezone.utc)
    d7  = [a for a in articles if now - _published_dt(a, now) <= timedelta(days=7)]
    d30 = [a for a in articles if now - _published_dt(a, now) <= timedelta(days=30)]
    return (d7 or articles[:20]), (d30 or articles)
