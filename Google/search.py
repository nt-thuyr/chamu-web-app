import pandas as pd
import requests
import urllib.parse
import os
import time
from dotenv import load_dotenv

# .envファイルからAPIキーを読み込む
load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# APIキーが存在しない場合はエラー
if not API_KEY:
    raise ValueError("APIキーが読み込めませんでした。`.env` を確認してください。")

# 入力CSVファイル（市区町村一覧）
input_path = "location.csv"

# 出力CSVファイル
output_path = "shop_rate.csv"

# 検索キーワード（変更可）
query_keyword = "海外料理　本場の味　レストラン　外国人店主"  #

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

    # Google Maps 検索URL
    search_url = f"https://www.google.com/maps/search/?api=1&query={url_encoded_query}"
    df.at[index, "検索URL"] = search_url

    # Google Places API リクエスト
    api_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": query,
        "key": API_KEY,
        "language": "ja"
    }

    try:
        response = requests.get(api_url, params=params, timeout=10)
        data = response.json()

        # デバッグ用出力（後で削除してOK）
        print(f"クエリ: {query}")
        print(f"ステータス: {data.get('status')}")
        print(f"件数: {len(data.get('results', []))}")
        print("-" * 40)

        # 検索結果件数を記録
        if data.get("results"):
            df.at[index, "検索件数"] = len(data["results"])
        else:
            df.at[index, "検索件数"] = 0

    except requests.exceptions.Timeout:
        print(f"タイムアウト: {query}")
        df.at[index, "検索件数"] = "timeout"

    except requests.exceptions.RequestException as e:
        print(f"通信エラー: {query} - {e}")
        df.at[index, "検索件数"] = "error"

    time.sleep(0.5)  # APIへの負荷軽減

# 出力ファイルが既に存在していれば削除
if os.path.exists(output_path):
    os.remove(output_path)

# 結果をCSVで出力（UTF-8）
df.to_csv(output_path, index=False, encoding="utf-8-sig")
