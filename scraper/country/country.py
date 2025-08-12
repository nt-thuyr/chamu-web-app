from bs4 import BeautifulSoup
import requests
import csv
import time

output_file = 'country_50.csv'
url = 'https://kikajapan.net/souzairyugaikokujinsuu/'


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
    'Referer': url,
    'Connection': 'keep-alive',
}


with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["number", "country_name"])

    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status() 
        soup = BeautifulSoup(res.text, 'html.parser')

        ranking_items = soup.select('table.ranking_table tbody tr')

        for i, item in enumerate(ranking_items):
            if i >= 50:
                break

            # サーバーに負荷をかけないよう、リクエスト間に遅延を入れる（この例ではループ内ではないが、習慣として重要）
            # time.sleep(1)

            cells = item.select('td')

            if len(cells) >= 2:
                rank = cells[0].text.strip()
                country_name = cells[1].text.strip()
                
                writer.writerow([rank, country_name])
                print(f"順位: {rank}, 国名: {country_name}")

    except requests.exceptions.RequestException as e:
        print(f"エラーが発生しました: {e}")

print(f"\nデータ抽出が完了しました。`{output_file}`に上位50位の国名を保存しました。")