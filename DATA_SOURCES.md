# Data Sources

This project enriches European travel destinations with coordinates, seasonal
weather, nearby places, and derived experience scores.

## Raw Destinations

Source file:

- `data/raw/european_destinations.csv`

Columns:

- `destination_name`: public destination name used in the product and final
  dataset.
- `search_name`: practical lookup name used by the data pipeline when a
  destination is an island, region, or broad travel area.
- `country`: destination country.
- `destination_type`: controls how broad the POI search should be. Examples:
  `city`, `coastal_city`, `island`, `region`, `mountain`.

`search_name` exists because some travel destinations are not precise points.
For example, `Kefalonia` is an island, so the pipeline uses `Argostoli` for
geocoding. This keeps the user-facing destination label intact while improving
the quality of coordinates and nearby-place counts.

Examples:

| destination_name | search_name | country | destination_type |
| --- | --- | --- | --- |
| Kefalonia | Argostoli | Greece | island |
| Mallorca | Palma de Mallorca | Spain | island |
| Sardinia | Cagliari | Italy | island |
| Cinque Terre | Monterosso al Mare | Italy | region |

## Coordinates

Source:

- OpenStreetMap Nominatim

Script:

- `src/collect_base_data.py`

Output:

- `data/processed/destinations_with_coordinates.csv`

The pipeline queries Nominatim with:

```text
search_name, country
```

and stores the resulting `latitude` and `longitude` alongside both
`destination_name` and `search_name`.

## Seasonal Weather

Source:

- Open-Meteo Archive API

Script:

- `src/collect_base_data.py`

Output:

- `data/processed/destinations_enriched_weather.csv`

The pipeline collects historical daily weather for 2023-01-01 through
2025-12-31 and aggregates it by season:

- `winter_avg_temp`
- `winter_avg_daily_rain`
- `spring_avg_temp`
- `spring_avg_daily_rain`
- `summer_avg_temp`
- `summer_avg_daily_rain`
- `autumn_avg_temp`
- `autumn_avg_daily_rain`

## Nearby Places And Attractions

Source:

- Overpass API using OpenStreetMap data

Script:

- `src/collect_places.py`

Output:

- `data/processed/destinations_with_places.csv`

The pipeline counts OpenStreetMap objects around each destination coordinate.
The search radius depends on `destination_type`, because a city, an island, and
a region should not be treated as the same spatial scale:

| destination_type | POI radius |
| --- | ---: |
| `city` | 3 km |
| `coastal_city` | 8 km |
| `mountain` | 5 km |
| `island` | 15 km |
| `region` | 15 km |

These counts should be interpreted as nearby/local POIs within the configured
radius, not as complete totals for an entire island or region. For beaches,
OpenStreetMap may count multiple mapped `natural=beach` features such as small
coves, beach segments, or coastline areas. In the user interface this raw value
is therefore treated as a beach access signal, not as an official number of
tourist beaches.

The dashboard maps the raw beach count to qualitative labels:

| nearby_beach_count | UI label |
| ---: | --- |
| 0-5 | Low |
| 6-20 | Moderate |
| 21-60 | High |
| 60+ | Excellent |

The same interpretation layer is used for other destination signals. Raw counts
remain available for scoring and analysis, while the dashboard shows qualitative
labels such as food scene, culture, nature, weather, and beach access so users
do not need to interpret raw OpenStreetMap counts directly.

For large islands or broad regions, this is a V1 approximation around one
representative location. A future version should sample multiple locations per
destination instead of using a very large radius from a single point.

Collected place features:

- `restaurant_count`: `amenity=restaurant`
- `cafe_count`: `amenity=cafe`
- `bar_count`: `amenity=bar`
- `museum_count`: `tourism=museum`
- `park_count`: `leisure=park`
- `nearby_beach_count`: `natural=beach`
- `search_radius_m`: radius used for the Overpass query

The script uses one batched Overpass request per destination and can resume
from `data/processed/places_partial.csv` when a previous run was interrupted or
rate-limited.

## Derived Scores

Script:

- `src/collect_places.py`

Output:

- `data/processed/destinations_with_places.csv`

Derived scores are normalized to a 0-100 scale within the current dataset:

- `food_score`: `restaurant_count + cafe_count`
- `nightlife_score`: `bar_count`
- `culture_score`: `museum_count`
- `nature_score`: `park_count`
- `beach_score`: `nearby_beach_count`

Scores are relative to the maximum value in the dataset, so they are useful for
ranking destinations against each other in this project dataset. They should be
recomputed whenever the destination list or place-count collection logic
changes.

## Destination Cost Proxy And Travel Cost Pipeline

V1 source file:

- `data/raw/destination_costs.csv`

V2 collection script:

- `src/collect_travel_costs.py`

Script:

- `src/feature_engineering.py`

Output:

- `data/processed/destinations_travel_costs.csv`
- `data/processed/destinations_feature_engineered.csv`

For V1, destination affordability is modeled with a `cost_of_living_index`
proxy. This is not a direct measure of tourist spending or hotel prices, but it
provides a consistent numerical signal for comparing destinations.

Derived cost labels:

| cost_of_living_index | cost_level |
| ---: | --- |
| `< 45` | Budget |
| `45-65` | Mid-range |
| `> 65` | Luxury |

The recommendation engine uses `cost_level` to calculate a `budget_match_score`
against the user's selected budget. The score is a soft ranking signal, not a
hard filter, because affordability is only one part of travel fit.

In this project:

- Budget preference = what the user selects: Low, Medium, or High.
- Travel cost level / `cost_level` = how expensive the destination is estimated
  to be.
- `budget_match_score` = the compatibility score between the user's budget
  preference and the destination's cost level.

Current implementation note: the V1 budget logic works, but `cost_level` is
based mainly on the fallback `cost_of_living_index`. The more realistic
`travel_cost_index` is a V2 upgrade that depends on Numbeo and Amadeus API keys.

Budget matching uses a gradual score matrix:

| User budget preference | Budget destination | Mid-range destination | Luxury destination |
| --- | ---: | ---: | ---: |
| Low (Essential) | 100 | 65 | 25 |
| Medium (Comfort) | 75 | 100 | 70 |
| High (Luxury) | 60 | 85 | 100 |

Limitation: seasonal hotel prices can differ from cost-of-living levels. For
example, a destination may have a mid-range local cost profile but become more
expensive during peak travel months.

For V2, the project introduces a travel-cost collection pipeline. It is designed
to collect:

- hotel prices within a configurable radius around the destination coordinates;
- restaurant meal prices;
- cappuccino/cafe prices;
- grocery basket prices;
- local transport prices;
- attraction or museum prices when a reliable source is available.

The pipeline uses environment variables for API credentials:

- `NUMBEO_API_KEY`
- `AMADEUS_CLIENT_ID`
- `AMADEUS_CLIENT_SECRET`

The output includes:

- `avg_hotel_price_eur`
- `median_hotel_price_eur`
- `restaurant_meal_price_eur`
- `cappuccino_price_eur`
- `groceries_basket_price_eur`
- `museum_or_attraction_price_eur`
- `local_transport_price_eur`
- `travel_cost_index`
- `travel_cost_level`
- `cost_data_coverage`

`travel_cost_index` is calculated as a weighted score:

| Component | Weight |
| --- | ---: |
| Hotel price | 45% |
| Restaurant meal price | 20% |
| Cafe price | 10% |
| Grocery basket price | 10% |
| Attraction price | 10% |
| Local transport price | 5% |

When `data/processed/destinations_travel_costs.csv` exists,
`feature_engineering.py` uses `travel_cost_level` as the main `cost_level`.
Otherwise, it falls back to the simpler V1 `cost_of_living_index` proxy.
