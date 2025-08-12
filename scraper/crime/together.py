import pandas as pd

# CSVファイルを読み込む
# crime_rank.csv: 「札幌市中央区」などの詳細なデータ
crime_data = pd.read_csv('crime_rank.csv')

# city_list.csv: 「札幌市」などの一般的な市区町村リスト
city_list_data = pd.read_csv('city_list.csv', header=None, names=['rank', 'prefecture', 'city_name'])

# --- データクレンジング（データの整形） ---
# `crime_data`の市区町村名を、`city_list_data`の表記に合わせる
# 例: 「札幌市中央区」 -> 「札幌市」
# 例: 「釧路郡」 -> 「釧路市」
crime_data['city_name_normalized'] = crime_data['city_name'].str.replace(r'(区|郡|町|村)$', '', regex=True)

# 例外処理：`crime_data`の「釧路郡」は、`city_list_data`では「釧路市」と表記されているため、修正する
crime_data['city_name_normalized'] = crime_data['city_name_normalized'].replace('釧路', '釧路市')


# --- データの統合 ---
# `city_list_data`を基準として、`crime_data`の整形済みデータとマージする
merged_data = pd.merge(
    city_list_data,
    crime_data,
    left_on=['prefecture', 'city_name'],
    right_on=['prefecture', 'city_name_normalized'],
    how='left'
)

# 不要な列を削除し、列の順序を整理する
merged_data = merged_data.drop(columns=['city_name_normalized']).rename(columns={'city_name_y': 'original_crime_city', 'city_name_x': 'city_name'})
merged_data = merged_data[['rank', 'prefecture', 'city_name', 'original_crime_city', 'percent']]

# 統合したデータを新しいCSVファイルとして出力
merged_data.to_csv('merged_crime_data.csv', index=False, encoding='utf-8-sig')

print("データ統合が完了しました。`merged_crime_data.csv`を出力しました。")

