# 🌍 Smart Travel

An end-to-end AI-powered travel recommendation system that combines geospatial data, historical weather, points of interest, feature engineering, clustering, and explainable recommendations to help users discover their ideal travel destination.

---

## ✨ Overview

Smart Travel is more than a machine learning project.

Instead of training a model on an existing dataset, the project builds a complete data pipeline that:

- collects real-world data from public APIs,
- enriches destinations with weather and geographic information,
- engineers travel-related features,
- discovers destination profiles using Machine Learning,
- generates explainable recommendations,
- exposes the recommendation engine through both a REST API and an interactive Streamlit dashboard.

The goal is to simulate a real-world data product rather than a standalone machine learning notebook.

---

# 🏗️ Project Pipeline

```text
Raw Destinations
        │
        ▼
Geocoding (Nominatim)
        │
        ▼
Weather Enrichment (Open-Meteo)
        │
        ▼
Points of Interest Collection (Overpass API)
        │
        ▼
Feature Engineering
        │
        ▼
Exploratory Data Analysis
        │
        ▼
K-Means Clustering
        │
        ▼
Recommendation Engine
        │
        ▼
FastAPI + Streamlit Dashboard
```

---

# 🚀 Features

- 🌍 Geocoding with OpenStreetMap (Nominatim)
- ☀️ Historical weather collection using Open-Meteo Archive API
- 🍝 Restaurant, café, museum, beach, park and nightlife extraction using Overpass API
- 📊 Exploratory Data Analysis
- ⚙️ Feature Engineering
- 🤖 K-Means clustering
- 🎯 Explainable recommendation engine
- 🌐 REST API with FastAPI
- 🎨 Interactive dashboard with Streamlit
- 🗺️ Interactive destination map

---

# 🧠 Machine Learning

The first recommendation model uses K-Means clustering.

The model learns destination profiles based on:

- Restaurant count
- Café count
- Bar count
- Museum count
- Park count
- Beach count
- Average summer temperature
- Average summer rainfall

All features are standardized using StandardScaler before training.

Although **k = 2** achieved the highest Silhouette Score, **k = 3** was selected because it produced more meaningful travel profiles.

Example clusters:

- 🏖️ Warm Coastal & Beach
- 🌿 Cool Balanced & Nature
- 🏙️ Urban Culture & Food

---

# 📂 Project Structure

```text
smart-travel/
│
├── dashboard/
│   └── streamlit_app.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── external/
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_exploratory_data_analysis.ipynb
│   ├── 03_feature_validation.ipynb
│   └── 04_machine_learning.ipynb
│
├── src/
│   ├── api.py
│   ├── recommend.py
│   ├── collect_base_data.py
│   ├── collect_places.py
│   ├── feature_engineering.py
│   ├── prepare_ml_features.py
│   └── evaluate_kmeans_clusters.py
│
├── requirements.txt
└── README.md
```

---

# 📊 Data Sources

The project integrates multiple public data sources.

| Source | Purpose |
|---------|----------|
| OpenStreetMap (Nominatim) | Geocoding |
| Open-Meteo Archive API | Historical weather |
| Overpass API | Restaurants, cafés, museums, beaches, parks, bars |

More details are available in:

- DATA_SOURCES.md

---

# ⚙️ Feature Engineering

The project creates several travel-oriented features, including:

- warm_destination
- cold_destination
- summer_destination
- winter_destination
- rain_risk
- climate_category
- island_destination
- mountain_destination
- coastal_destination
- city_destination
- overall_score
- balanced_destination
- dominant_travel_style

More information:

- FEATURE_ENGINEERING.md

---

# 🖥️ Dashboard

The Streamlit dashboard allows users to:

- choose their travel month
- describe the type of trip they are looking for
- select activities and preferences
- receive explainable destination recommendations
- explore destinations on an interactive map

---

# 🔌 API

The recommendation engine is also available through FastAPI.

Example request:

```json
{
  "food": 8,
  "beach": 9,
  "culture": 3,
  "nature": 6,
  "nightlife": 4,
  "month": "August",
  "top_n": 5
}
```

The API returns ranked destinations together with recommendation scores and explanations.

---

# 💻 Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/smart-travel.git
cd smart-travel
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it:

Windows

```bash
source venv/Scripts/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# ▶️ Run the Dashboard

```bash
streamlit run dashboard/streamlit_app.py
```

Open:

```
http://localhost:8501
```

---

# ▶️ Run the API

```bash
uvicorn src.api:app --reload
```

Swagger documentation:

```
http://localhost:8000/docs
```

---

# 📸 Screenshots

## Dashboard

_Add screenshots here._

## Recommendation Results

_Add screenshots here._

## Interactive Map

_Add screenshots here._

---

# 🛠️ Tech Stack

- Python
- Pandas
- NumPy
- Scikit-learn
- Matplotlib
- Seaborn
- Streamlit
- FastAPI
- Folium
- Requests
- OpenStreetMap
- Open-Meteo API
- Overpass API

---

# 📌 Future Improvements

- Monthly weather features
- Hotel and flight price integration
- LLM-powered travel assistant
- Personalized user accounts
- Collaborative filtering
- Real-time weather forecasts
- Destination image generation

---

# 👩‍💻 Author

**Catinca Marinescu**

Business Informatics Graduate

Passionate about Data Science, Machine Learning, Artificial Intelligence, and building data-driven products.
