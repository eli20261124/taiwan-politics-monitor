import re
import html
import time
import jieba
from collections import Counter

_STOP = {
    "的","了","在","是","我","有","和","就","不","人","都","一","上",
    "也","很","到","說","要","去","你","會","著","看","好","自己","這",
    "他","她","它","我們","你們","他們","但","而","與","及","或","於",
    "台灣","記者","報導","新聞","表示","指出","相關","目前","已經",
}

_TAG_RE = re.compile(r"<[^>]+>")

_POLITICS_KW = {"政治","政府","選舉","立法院","總統","民進黨","國民黨","政策","外交","兩岸",
                "立委","行政院","內閣","罷免","修憲","公投","抗議","示威","爭議","法案"}
_FINANCE_KW  = {"金融","股市","經濟","匯率","央行","投資","漲","跌","市場","利率",
                "通膨","貿易","出口","企業","財政","預算","上市","基金","債券","外資"}

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


def classify(article: dict) -> str:
    text  = article.get("title", "") + article.get("description", "")
    words = set(jieba.cut(_clean(text)))
    if len(words & _FINANCE_KW) >= len(words & _POLITICS_KW):
        return "finance"
    return "politics"


def sector_split(articles: list[dict]) -> tuple[list[dict], list[dict]]:
    politics, finance = [], []
    for a in articles:
        (finance if classify(a) == "finance" else politics).append(a)
    return politics, finance


def _recency_score(article: dict, now: float) -> float:
    age_s = now - article.get("published", now)
    return max(0.0, 1.0 - age_s / 86400)


def rank_articles(articles: list[dict], top_n: int = 5) -> list[dict]:
    now      = time.time()
    all_freq = Counter(_words(_text_from(articles)))
    scored   = []
    for a in articles:
        density = sum(all_freq[w] for w in _words(a.get("title", "")))
        score   = _recency_score(a, now) * 0.6 + min(density / 50, 1.0) * 0.4
        scored.append((score, a))
    scored.sort(key=lambda x: x[0], reverse=True)
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
    Falls back to most-recent 20 (for h1) or all articles (for h12) if the
    window is empty (e.g. slow news period).
    """
    import time as _time
    now  = _time.time()
    h1   = [a for a in articles if now - a.get("published", now) <= 3_600]
    h12  = [a for a in articles if now - a.get("published", now) <= 43_200]
    return (h1 or articles[:20]), (h12 or articles)
