import os
from dotenv import load_dotenv

load_dotenv()

QUERIES          = os.getenv("MONITOR_QUERIES", "台灣 政治 爭議,台灣 金融 市場").split(",")
LANGUAGE_CODE    = os.getenv("LANGUAGE_CODE", "zh-TW")

REPORT_PATH      = os.getenv("REPORT_PATH",      "daily_report.json")
HTML_REPORT_PATH = os.getenv("HTML_REPORT_PATH", "index.html")
