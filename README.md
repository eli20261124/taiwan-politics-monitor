# 🏛️ 台灣政經戰情室
**Taiwan Finance & Politics Intelligence Monitor**

自動抓取 Google News RSS，分析台灣政治、金融輿情，並生成互動式 HTML 儀表板。**每小時由 GitHub Actions 自動更新**，部署至 GitHub Pages。

---

## ✨ 功能簡介

| 功能 | 說明 |
|------|------|
| 📡 自動抓取新聞 | 透過 Google News RSS，免費、零 API 費用 |
| 🕐 雙時段對比 | 近 1 小時 vs 近 12 小時，感知輿情變化 |
| 🏛️ 政黨標籤識別 | 自動偵測 KMT / DPP / TPP 關鍵字 |
| 🧨 政黨攻防偵測 | 同時出現多黨關鍵字時標記為「政黨攻防」 |
| 🏙️ 六都熱度分析 | 台北、新北、桃園、台中、台南、高雄 |
| 📊 流量排行榜 | 結合時效性 + 關鍵字密度計算熱度分數 |
| 🔒 PII 過濾 | 自動遮蔽 email、電話、身分證字號 |
| 🌏 全球市場行情 | 亞洲 / 美股 / 大宗商品 10 檔指數即時報價（yfinance） |
| ⏰ 每小時自動刷新 | GitHub Actions 排程，commit 更新後自動重新部署 |
| 🛡️ 容錯抓取 | 單一來源逾時不影響整體儀表板產出 |

---

## 🖥️ 圖示說明

| 圖示 | 代表意義 |
|------|----------|
| 🟦 | KMT 國民黨 |
| 🟩 | DPP 民進黨 |
| ⬜ | TPP 民眾黨 |
| 🔴 | 其他 / 無黨籍 |
| 🧨 | **政黨攻防**：文章同時偵測到多個政黨關鍵字，代表有跨黨衝突或論戰 |
| 🔴 Volatile | 文章含有衝突性關鍵字（跌、危機、抗議…） |
| 🟢 Stable | 文章含有穩定性關鍵字（成長、合作、突破…） |
| ⚪ Neutral | 情緒中性 |

---

## 🚀 快速開始

### 1. 安裝環境

```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 設定環境變數（可選）

複製範例設定：
```bash
cp .env.example .env
```

預設不需修改即可運行；若要自訂查詢關鍵字，編輯 `.env`：
```
MONITOR_QUERIES=台灣 政治 爭議,台灣 金融 市場,台灣 AI 科技
```

### 3. 執行

```bash
python monitor.py
```

產出：
- `index.html` — 互動式儀表板，用瀏覽器開啟即可
- `daily_report.json` — 結構化資料

```bash
open index.html   # macOS
```

---

## 📁 檔案結構

```
.
├── monitor.py              # 主程式入口
├── fetcher.py              # Google News RSS 抓取 + 市場資料彙整（容錯）
├── analyzer.py             # NLP 分析（jieba 斷詞、政黨偵測、六都分析）
├── reporter.py             # HTML 報告生成（含右側欄市場 + 行事曆）
├── security.py             # PII 過濾（email / 電話 / 身分證）
├── config.py               # 環境設定
├── requirements.txt        # Python 依賴
├── .env.example            # 環境變數範例
└── .github/
    └── workflows/
        ├── main.yml        # ⏰ 每小時執行 monitor.py 並 commit/push
        └── deploy.yml      # 🚀 Push 到 main 後自動部署至 GitHub Pages
modules/
└── market/
    ├── global_markets.py   # 10 檔全球指數抓取（Asia / USA / Commodities）
    └── tw_index.py         # 向下相容 shim
```

---

## 🛡️ 安全性說明

- **無硬編碼金鑰**：所有設定皆由 `os.getenv()` 讀取
- **`.env` 已加入 `.gitignore`**，不會上傳至 GitHub
- **不需要任何付費 API**：僅使用公開的 Google News RSS

---

## 📦 依賴套件

| 套件 | 用途 |
|------|------|
| `feedparser` | 解析 RSS Feed |
| `jieba` | 繁體中文斷詞 |
| `python-dotenv` | 讀取 `.env` 設定 |
| `yfinance` | 全球股市 / 大宗商品即時行情 |

---

## 🌐 GitHub Pages 部署

Push 到 `main` 分支後，`deploy.yml` 會自動將 `index.html` 部署至 GitHub Pages。

設定方式：GitHub repo → Settings → Pages → Source: GitHub Actions

---

## ⏰ 自動更新機制

`main.yml` 每整點執行一次（UTC `0 * * * *`）：

1. 執行 `python monitor.py` 重新抓取新聞與市場資料
2. 若 `index.html` 或 `daily_report.json` 有變動，自動 commit 並 push
3. Push 觸發 `deploy.yml`，更新 GitHub Pages

> 可在 GitHub repo → Actions → **Hourly Dashboard Update** → **Run workflow** 手動觸發。

---

*儀表板每小時自動刷新，無需手動操作。*

## 🧠 數據處理與排名演算法 (Data Processing & Ranking Algorithm)

本監測站不只是簡單的新聞聚合器，而是透過一套精密的自動化管線進行數據清洗與權重排序。

### 1. 多維度抓取矩陣 (Multi-Channel Fetching)
為了突破單一 RSS 接口的數量限制（約 100 則），本專案採用了**關鍵字矩陣策略**：
* **子查詢拆解**：針對「金融、房市、政治、AI、國際」五大板塊，各設定 10-15 組專業子關鍵字。
* **來源鎖定**：整合 Google News 與特定權威媒體（如：經濟日報、自由地產等）的精確過濾語法。
* **海量數據**：單次抓取總量超過 **2,500 則**，確保不漏掉任何細分領域的新聞。

### 2. 智能去重邏輯 (Deduplication)
* **URL 唯一性檢查**：透過 Python 的 `set` 與雜湊邏輯，過濾掉不同關鍵字抓取到的重複報導。
* **語義聚合**：針對同一事件的不同媒體報導，系統會記錄其被提及的頻次（Count），作為後續熱度計算的基礎。

### 3. 熱度評分演算法 (Ranking with Time Decay)
我們採用了**時間衰減重力公式**，確保「最新」且「最受關注」的新聞能排在第一位，而非舊聞霸榜。

#### **核心數學公式：**
$$Score = \frac{Count}{(Hours\_Old + 1)^{1.8}} \times Boost$$

* **$Count$ (累積頻次)**：該新聞在不同子查詢中被掃描到的總次數。
* **$Hours\_Old$ (時差)**：從新聞發布到現在的小時數。
* **$1.8$ (重力係數)**：隨著時間流逝，新聞分數會呈指數級衰減，確保「1H 區塊」的動態新鮮度。

#### **加成係數 (Boost Strategy)：**
* **新鮮度獎勵 (Freshness Bonus)**：若新聞發布於 **45 分鐘內**，分數自動乘以 **1.5 倍**。
* **來源多樣性獎勵 (Diversity Bonus)**：若新聞在超過 **3 個獨立來源** 同時出現，額外給予 **20% 權重**。

### 4. 動態時間窗口 (Adaptive Windowing)
* **1H 嚴格窗口**：預設僅顯示 1 小時內之新聞。
* **緩衝機制 (Minimum Buffer)**：若該時段新聞不足 5 則，系統自動將窗口延展至 3 小時，確保內容豐富度，並自動更新 UI 標籤。

---

## ⚖️ 授權條款 (License)

本專案採用 **MIT License** 授權。

Copyright (c) 2026 eli20261124

特此授權任何取得本軟體副本的人士，在不受限制的情況下處理本軟體，包括但不限於使用、複製、修改、合併、發佈、分發、再授權及/或出售軟體的副本，並允許軟體供應對象在遵守以下條件的前提下執行上述操作：

**上述版權聲明和本許可聲明應包含在軟體的所有副本或主要部分中。**
