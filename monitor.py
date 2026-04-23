import os
from dotenv import load_dotenv
from apify_client import ApifyClient

load_dotenv()
client = ApifyClient(os.getenv("APIFY_API_TOKEN"))

run_input = {
    "queries": "台灣 政治 爭議",
    "maxPagesPerQuery": 1,
    "resultsPerPage": 5,
    "mobileResults": False,
    "languageCode": "zh-TW",
    "locationCode": "Taiwan",
    "timeRange": "d", # 過去 24 小時
}

run = client.actor("apify/google-search-scraper").call(run_input=run_input)

for result in client.dataset(run["defaultDatasetId"]).iterate_items():
    for organic in result.get("organicResults", []):
        print(f"Title: {organic['title']}\nLink: {organic['url']}\n")