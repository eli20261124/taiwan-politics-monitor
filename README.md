# 🏛️ 台灣政經戰情室
**Taiwan Finance & Politics Intelligence Monitor**

自動抓取 Google News RSS，分析台灣政治、金融輿情，並生成互動式 HTML 儀表板。

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
├── monitor.py        # 主程式入口
├── fetcher.py        # Google News RSS 抓取
├── analyzer.py       # NLP 分析（jieba 斷詞、政黨偵測、六都分析）
├── reporter.py       # HTML 報告生成
├── security.py       # PII 過濾（email / 電話 / 身分證）
├── config.py         # 環境設定
├── requirements.txt  # Python 依賴
├── .env.example      # 環境變數範例
└── .github/
    └── workflows/
        └── deploy.yml  # GitHub Pages 自動部署
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

---

## 🌐 GitHub Pages 部署

Push 到 `main` 分支後，GitHub Actions 會自動將 `index.html` 部署至 GitHub Pages。

設定方式：GitHub repo → Settings → Pages → Source: GitHub Actions

---

*自動生成的儀表板每次執行後會覆蓋 `index.html`，推送至 GitHub 即可更新網頁。*
