import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

query = "横浜市 海外ショップ"
url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

params = {
    "query": query,
    "key": API_KEY,
    "language": "ja"
}

total_results = 0
page_count = 0
next_page_token = None

while page_count < 3:
    if next_page_token:
        params["pagetoken"] = next_page_token
        time.sleep(2)  # トークンが有効になるまで最大2秒必要

    response = requests.get(url, params=params)
    data = response.json()

    # 件数を加算
    results = data.get("results", [])
    total_results += len(results)

    # 次ページトークンがあるか確認
    next_page_token = data.get("next_page_token")
    if not next_page_token:
        break  # 次ページがないなら終了

    page_count += 1

print("合計ヒット件数:", total_results)
