from bs4 import BeautifulSoup
import requests
res = requests.get('https://www.orangepage.net/recipes/ingredients/%E9%87%8E%E8%8F%9C/%E6%A0%B9%E8%8F%9C/%E3%81%AB%E3%82%93%E3%81%98%E3%82%93')
soup = BeautifulSoup(res.text,'html.parser')
h2_tags = soup.find_all('h2')
h2_strings = [x.string for x in h2_tags]
print(h2_strings[0])