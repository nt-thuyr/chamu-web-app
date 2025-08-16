# 🏠 住みたい日本ナビ (Sumitai Nihon Navi) - Japan Housing Navigator

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/Django-4.0+-green.svg)](https://www.djangoproject.com/)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)](https://sqlite.org/)
[![Folium](https://img.shields.io/badge/Folium-77B829?logo=folium&logoColor=white)](https://folium.readthedocs.io/)
[![Wikipedia](https://img.shields.io/badge/Wikipedia-000000?logo=wikipedia&logoColor=white)](https://wikipedia.org/)

🌍 A comprehensive web application designed to help foreign residents who want to move and find new places to live in Japan through intelligent matching algorithms and community-driven evaluations.

⚠️ **Project Status**: This is an **educational prototype project** developed for Global Project-Based Learning (gPBL) 2025.  
Not intended for commercial or production use.

---

## 🌟 Features
- 🎯 Smart Location Matching (weighted scoring algorithm)  
- 🗺️ Interactive Map Interface (Folium)  
- 👥 Community Evaluation System (evaluates municipalities on 5 criteria: **Price, Population Density, Crime Rate, Cultural Food Availability, and Temperature**)
- 🌏 Cultural Customization by nationality  
- ⚡ Real-time Score Updates (objective + subjective feedback)  

---

## ⚙️ Scoring Algorithm

Our scoring system is built on a multi-layered approach for reliable and personalized recommendations.

### 1. Final Score
**Combines objective data with community feedback:** 

`Final Score = (Base Score × 0.6) + (User Reviews Average × 0.4)`

### 2. Matching Score
**Customizes results based on user priorities:**

`Matching Score = Σ(Individual Score × Priority Weight) / Total Weight`


### 3. Match Percentage
**Converts the final score into a clear percentage:**

`Match Percentage = ((Max Score - User Score) / Score Range) × 100%`

---

## 📸 Demo / Screenshots
### Matching Flow Views
<p float="left">
  <img src="docs/screenshots/homepage.png" width="300" />
  <img src="docs/screenshots/match_info.png" width="300" />
  <img src="docs/screenshots/matching_survey.png" width="300" />
</p>

<p float="left">
  <img src="docs/screenshots/matching_results.png" width="300" />
  <img src="docs/screenshots/municipality_details.png" width="300" />
</p>

### Evaluation Flow Views
<p float="left">
  <img src="docs/screenshots/evaluate_info.png" width="300" />
  <img src="docs/screenshots/evaluation_survey.png" width="300" />
  <img src="docs/screenshots/thank_you.png" width="300" />
</p>

### Other
<p float="left">
  <img src="docs/screenshots/about.png" width="300" />
</p>

---

## 🚀 Getting Started

### Prerequisites
```bash
Python 3.8+
pipenv
Git
```

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/sumitai-nihon-navi.git
cd sumitai-nihon-navi
```

2. **Install dependencies with pipenv**
```bash
pipenv install
```

3. **Run the development server**
```bash
pipenv run python manage.py runserver
```

Then visit: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 📱 Usage

### Matching Flow 🏠➡️🏠
1. Input personal information  
2. Rank evaluation criteria by importance  
3. View matched municipalities with compatibility scores  
4. Explore municipality details (Wikipedia, map, breakdowns)  

### Evaluation Flow 🤝📊
1. Input your current location info  
2. Rate your area (1–5 stars per criterion)  
3. Compare with community averages  
4. Contribute to improve recommendations  

---

## ⚠️ Known Issues / Limitations
- No authentication system yet (anonymous usage)  
- Limited evaluation criteria (only 5 basic ones)  
- Data sources limited to Wikipedia + manual input  
- No weather/transport API integration yet  
- Prototype UI – not optimized for production  

---

## 👥 Development Team <img src="https://upload.wikimedia.org/wikipedia/commons/2/21/Flag_of_Vietnam.svg" width="20"> <img src="https://upload.wikimedia.org/wikipedia/en/9/9e/Flag_of_Japan.svg" width="20">
**Team Chamu** 
- **孫　美結** (Son Miyu)  
- **青木　恵** (Aoki Megumi)  
- **Thái Mỹ Anh**  
- **Nguyễn Thanh Thủy**  

---

## 🔮 Future Roadmap
- 🌐 Multi-language Interface (English, Vietnamese)  
- 📧 Gmail OAuth2 login  
- 🕷️ Web scraping + Google Maps API  
- 📚 More evaluation criteria (education, healthcare, transport)  
- 📱 Mobile App (React Native / Flutter)  
- 🏠 Real Estate integration  
- 🚌 Transport & commute time analysis  
- 💬 Community comments  
- 🤖 Machine Learning for recommendations  
- 📊 Live data feeds (weather, events, news)  

---

## 📄 License
This project is not licensed for commercial use. It is for **educational purposes only**.

---

## 📬 Contact
For questions or feedback, please contact us via GitHub Issues:  
👉 [GitHub Repository](https://github.com//sumitai-nihon-navi)

---

**Made with ❤️ by Team Chamu - Bridging cultures through technology**
