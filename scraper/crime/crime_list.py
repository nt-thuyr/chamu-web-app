from bs4 import BeautifulSoup
import requests
import csv


output_file = 'crime_rank.csv'

with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["prefecture", "city_name", "percent"])

    with open('pref_list.txt', 'r', encoding='utf-8') as f:
        prefectures = [line.strip() for line in f.readlines() if line.strip()]

    for pref in prefectures:
        page = 1 
        while True:
            url = f'https://sumaity.com/town/ranking/{pref}/crime/?page={page}'
            res = requests.get(url)
            soup = BeautifulSoup(res.text,'html.parser')


            city_data_boxs = soup.select('dl.machiRevBoxRank, dl.machiRevBoxRank2')
            if not city_data_boxs: 
                break


            for city_data_box in city_data_boxs:    

                city_name_tag = city_data_box.find('a')
                city_name = city_name_tag.text.strip() if city_name_tag else 'no' #stripは空白失くす

                percent_tag = city_data_box.find("dd", class_="ageAve")
                em_tag = percent_tag.find("em") if percent_tag else 'no'
                percent_value = percent_tag.text.strip().replace('%', '').strip() if percent_tag else 'no'

    
                print(f"{pref}, {city_name}, {percent_value}%")


                writer.writerow([pref, city_name, percent_value])
        
            page += 1

