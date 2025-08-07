import pandas as pd
import requests
import urllib.parse
import os

# 入力CSVファイル（市区町村一覧）
input_path = "location.csv"

# 出力CSVファイル
output_path = "海外ショップ検索リンク.csv"

# Google Maps APIキー（自分のものに置き換えてください）
API_KEY = "YOUR_GOOGLE_MAPS_API_KEY"  # ←★ここに自分のAPIキーを入力

# 検索キーワード
query_keyword = "海外ショップ"

# CSV読み込み（Shift-JIS対応）
df = pd.read_csv(input_path, encoding="shift_jis")

# 結果用のカラムを追加
df["検索URL"] = ""
df["検索件数"] = ""

# 各市区町村ごとに処理
for index, row in df.iterrows():
    location = f"{row['都道府県']}{row['市区町村']}"
    query = f"{location} {query_keyword}"
    url_encoded_query = urllib.parse.quote(query)

    search_url = f"https://www.google.com/maps/search/?api=1&query={url_encoded_query}"
    df.at[index, "検索URL"] = search_url

    # Google Maps Places API で検索件数を取得
    api_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": query,
        "key": API_KEY,
        "language": "ja"
    }
    response = requests.get(api_url, params=params)
    data = response.json()

    # 結果数取得（最大 20 件／ページ）
    if data.get("results"):
        df.at[index, "検索件数"] = len(data["results"])
    else:
        df.at[index, "検索件数"] = 0

# CSV書き出し（出力ファイルを開いてるとエラーになるので注意）
if os.path.exists(output_path):
    os.remove(output_path)

df.to_csv(output_path, index=False, encoding="utf-8-sig")
