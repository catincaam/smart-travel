# Smart Travel

Smart Travel is an end-to-end travel recommendation system. It collects and
combines geospatial, weather, point-of-interest, cost proxy, clustering, and
preference data to recommend destinations in an explainable way.

The project is designed as a data product, not only as a notebook experiment:

```text
raw destinations
    -> geocoding
    -> seasonal weather
    -> nearby places and attractions
    -> feature engineering
    -> EDA
    -> clustering
    -> recommendation engine
    -> FastAPI
    -> Streamlit dashboard
```

## Highlights

- Automated data collection from Nominatim, Open-Meteo, and Overpass/OpenStreetMap.
- Adaptive POI radius by destination type.
- Feature engineering for food, nightlife, culture, nature, beach access,
  climate, and cost.
- K-Means clustering for interpretable destination profiles.
- Content-based recommendation engine with explainable scoring.
- Streamlit dashboard with tourist-friendly inputs instead of raw ML sliders.
- FastAPI endpoint for programmatic recommendations.
- Automated tests for preference translation and recommendation scoring.

## Project Structure

```text
smart-travel/
├── dashboard/
│   ├── assets/destinations/
│   └── streamlit_app.py
├── data/
│   ├── raw/
│   └── processed/
├── docs/
│   └── screenshots/
├── maps/
│   └── smart_travel_map.html
├── notebooks/
├── src/
│   ├── api.py
│   ├── collect_base_data.py
│   ├── collect_places.py
│   ├── feature_engineering.py
│   ├── preference_translation.py
│   └── recommend.py
├── tests/
├── DATA_SOURCES.md
├── FEATURE_ENGINEERING.md
├── PROJECT_EXPLANATION.md
├── TODO.md
└── README.md
```

## Screenshots

Dashboard screenshots should be saved in:

```text
docs/screenshots/
```

Recommended files:

```text
docs/screenshots/dashboard.png
docs/screenshots/recommendations.png
docs/screenshots/map.png
```

The local Streamlit app is dynamic, so screenshots are best captured from the
visible browser after running the dashboard.

## Run the API

Install dependencies:

```bash
pip install -r requirements.txt
```

Start FastAPI:

```bash
uvicorn src.api:app --reload
```

Interactive API docs:

```text
http://127.0.0.1:8000/docs
```

Main endpoint:

```text
POST /recommend
```

Example request:

```json
{
  "food": 8,
  "beach": 9,
  "culture": 3,
  "nature": 6,
  "nightlife": 4,
  "month": "August",
  "budget": "Medium (Comfort)",
  "top_n": 5
}
```

Each recommendation includes an explainable `reason` object and a natural-language `natural_reason`.

The recommender also supports budget matching. V1 uses
`cost_of_living_index` as an affordability proxy and derives:

- `Budget`: index below 45
- `Mid-range`: index from 45 to 65
- `Luxury`: index above 65

Terminology used in the project:

- `budget` / budget preference: what the user selects in the UI
  (`Low (Essential)`, `Medium (Comfort)`, or `High (Luxury)`).
- `cost_level` / travel cost level: how expensive the destination is estimated
  to be.
- `budget_match_score`: how well the user's budget preference matches the
  destination's `cost_level`.
- `cost_score`: the cost component used in the final recommendation formula.
  In V1, this is equal to `budget_match_score`.

This is a soft scoring signal, not a hard filter, because cost of living is not
the same as exact tourist spending or seasonal hotel prices. Budget currently
contributes 15% to the recommendation score, so selecting Low / Medium / High
can change the ranking without completely overriding travel preferences.

The V1 formula is:

```text
recommendation_score =
    0.60 * preference_score
  + 0.20 * weather_score
  + 0.15 * cost_score
  + cluster_bonus
  - must_have_penalty
```

The budget match is intentionally gradual rather than a strict exact-match rule:

| User budget preference | Budget destination | Mid-range destination | Luxury destination |
| --- | ---: | ---: | ---: |
| Low (Essential) | 100 | 65 | 25 |
| Medium (Comfort) | 75 | 100 | 70 |
| High (Luxury) | 60 | 85 | 100 |

Current V1 budget support is functional, but `cost_level` is still based mainly
on the fallback `cost_of_living_index`. A real `travel_cost_index` is prepared
for V2 and will replace the fallback once Numbeo and Amadeus API keys are
available.

## Travel Cost Pipeline V2

For a more realistic travel-cost model, the project includes:

```bash
python src/collect_travel_costs.py --month August --radius-km 3
```

The script is designed to collect hotel, restaurant, cafe, grocery, transport,
and attraction cost signals. It uses API credentials from environment variables:

```text
NUMBEO_API_KEY
AMADEUS_CLIENT_ID
AMADEUS_CLIENT_SECRET
```

Copy `.env.example` to `.env` locally and fill in your keys. The `.env` file is
ignored by Git.

Output:

```text
data/processed/destinations_travel_costs.csv
```

Then regenerate feature engineering:

```bash
python src/feature_engineering.py
```

When travel-cost data exists, `cost_level` is based on `travel_cost_level`.
Otherwise, the project falls back to the simpler V1 `cost_of_living_index`.

## Create The Interactive Map

Generate the Folium map:

```bash
python src/create_interactive_map.py
```

Open:

```text
maps/smart_travel_map.html
```

The map includes separate layers for summer weather, beach score, and culture score.

## Run The Streamlit Dashboard

Start the dashboard:

```bash
streamlit run dashboard/streamlit_app.py
```

Open:

```text
http://127.0.0.1:8501
```

The dashboard asks tourist-friendly questions, translates them into recommendation signals, and shows explainable Top N recommendations with the interactive map.

## Run Tests

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the automated tests:

```bash
python -m pytest
```

If the local Windows virtual environment has a stale interpreter path, use the
more robust form:

```bash
venv\Scripts\python.exe -c "import pytest, sys; sys.exit(pytest.main(['-q']))"
```

Current test coverage focuses on:

- preference translation rules;
- travel companion effects;
- free-text keyword extraction;
- weather preference inference;
- budget/cost score matching;
- recommendation output shape.

## Preference Translation

The dashboard no longer asks users to manually enter numeric ML weights such as
`food = 8` or `beach = 9`.

Instead, users answer natural travel-planning questions:

- trip type;
- travel companion;
- budget;
- preferred weather;
- must-do activities;
- short free-text description.

These answers are translated by `src/preference_translation.py` into internal
numeric signals:

```text
food / beach / culture / nature / nightlife
```

The translation logic is configuration-driven. Trip styles, activity weights,
travel companion effects, weather options, and text keyword rules are stored in
dictionaries inside `PREFERENCE_TRANSLATION_RULES`, instead of being scattered
across many hard-coded `if` statements.

Those signals are then passed to `src/recommend.py`, which calculates the final
recommendations.

The free-text field uses lightweight keyword extraction with synonyms and simple
typo tolerance. For example, `warm beach with good food` increases the beach and
food signals and can infer `Warm` as the weather preference when the user leaves
weather as `Any`. A phrase such as `weather good enough to go for a hike`
increases the nature signal and infers `Mild` weather.

Travel companion is not only a UI label. It changes the internal recommendation
signals before scoring:

| Travelling with | Preference adjustment |
| --- | --- |
| Solo | `culture +2`, `food +1` |
| Partner | `beach +2`, `food +2`, `nightlife +1` |
| Friends | `nightlife +3`, `food +2` |
| Family | `nature +2`, `culture +1`, `nightlife -2` |

Preferred weather is handled as a separate weather-fit signal:

| Preferred weather | Comfort curve |
| --- | --- |
| Warm | Highest score around `27C`, with gradual penalties away from that point |
| Mild | Highest score around `21C`, with gradual penalties away from that point |
| Cool | Highest score around `15C`, with gradual penalties away from that point |
| Any | Uses a general comfort temperature inferred from trip intent |

This affects `weather_score`, which contributes 20% to the final
recommendation score.

## Clustering Evaluation

The project uses K-Means to discover natural destination profiles, but it also
includes a comparison script:

```bash
python src/compare_clustering_algorithms.py
```

Output:

```text
data/processed/clustering_algorithm_comparison.csv
```

This compares K-Means, Hierarchical Clustering, and DBSCAN. K-Means remains the
V1 choice because it gives every destination an interpretable profile, while
some DBSCAN settings mark many destinations as noise.

## POI Search Logic

OpenStreetMap POI counts use an adaptive radius based on `destination_type`:

- `city`: 3 km
- `coastal_city`: 8 km
- `island`: 15 km
- `region`: 15 km
- `mountain`: 5 km

`nearby_beach_count` means beaches found around the representative location
within that radius. It is not the total number of beaches in an entire island
or region. Because OpenStreetMap can store small coves, coastline segments, and
beach areas as separate `natural=beach` features, the dashboard presents this as
a beach access level instead of a literal official beach total.

Beach access labels use simple thresholds:

- `0-5`: Low
- `6-20`: Moderate
- `21-60`: High
- `60+`: Excellent

The dashboard applies the same product principle to other raw POI counts:
restaurants, cafes, museums, parks, and beaches remain numeric backend
features, while the user interface presents qualitative travel signals such as
`Excellent food scene`, `High beach access`, or `Moderate culture`.

For large islands and regions, V1 uses one representative location. A future
version should sample multiple points instead of expanding one radius too far.
