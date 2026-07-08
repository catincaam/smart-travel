# Feature Engineering

Sprint 4 transforms the enriched travel dataset into a modeling-ready dataset.

Input:

- `data/processed/destinations_with_places.csv`

Output:

- `data/processed/destinations_feature_engineered.csv`

Script:

- `src/feature_engineering.py`

## Why Feature Engineering?

Raw values such as `restaurant_count`, `nearby_beach_count`, and `summer_avg_temp`
are useful, but they are not always the best direct representation of traveler
intent.

Feature engineering turns raw data into more meaningful signals:

- climate preferences
- destination type
- experience intensity
- balanced destination behavior
- explainable recommendation reasons

## Climate Features

| Feature | Rule | Reason |
| --- | --- | --- |
| `warm_destination` | `summer_avg_temp >= 24` | Identifies destinations suitable for warm-weather travel. |
| `cold_destination` | `winter_avg_temp < 5` | Captures destinations with colder winter profiles. |
| `summer_destination` | `summer_avg_temp >= 24` and `summer_avg_daily_rain <= 1.5` | Combines warmth with low summer rain. |
| `winter_destination` | `winter_avg_temp < 5` | Useful for mountain or cold-season recommendations. |
| `rain_risk` | max seasonal daily rain > 3 mm | Flags destinations where rain may affect travel planning. |
| `climate_category` | Warm, Mild, or Cool | Simplifies numeric weather into interpretable labels. |

Climate category rules:

- `Warm`: `summer_avg_temp >= 24` and `winter_avg_temp >= 10`
- `Cool`: `summer_avg_temp < 22` or `winter_avg_temp < 2`
- `Mild`: all other destinations

## Destination Type Features

| Feature | Rule | Reason |
| --- | --- | --- |
| `island_destination` | `destination_type == island` when available, otherwise fallback list | Some destinations are islands even if geocoded through a city. |
| `mountain_destination` | `destination_type == mountain` when available, otherwise fallback list | Captures known mountain or alpine destinations. |
| `coastal_destination` | `destination_type` in coastal/island/region types when available, otherwise fallback list | Captures coast-oriented travel experiences. |
| `city_destination` | Top 40% by restaurant + cafe + bar + museum density | Identifies destinations with strong urban POI density. |

`destination_type` is also used earlier in the pipeline to choose a more
appropriate Overpass search radius. For example, cities use a smaller radius
than islands or regions.

## Experience Features

| Feature | Rule | Reason |
| --- | --- | --- |
| `food_scene_intensity` | Min-max normalized restaurant + cafe count | Measures food density on a 0-100 scale. |
| `nightlife_intensity` | Min-max normalized bar count | Measures nightlife density on a 0-100 scale. |
| `cultural_density` | Min-max normalized museum count | Measures cultural POI density. |
| `nature_density` | Min-max normalized park + beach count | Measures nature and outdoor POI density. |
| `overall_score` | Average of food, nightlife, culture, nature, beach scores | Provides a simple broad appeal score. |
| `score_balance_std` | Standard deviation across the five main scores | Lower values mean a more balanced destination profile. |
| `balanced_destination` | `score_balance_std <= 15` | Flags destinations that perform consistently across categories. |
| `dominant_travel_style` | Highest style score, or Balanced if close | Creates an interpretable destination label. |

Dominant travel style uses:

- `Beach`: `beach_score`
- `Nature`: `nature_score`
- `Culture`: `culture_score`
- `Food & Nightlife`: average of `food_score` and `nightlife_score`
- `Balanced`: selected when the best style is within 10 points of the second best

## Cost Features

Cost is modeled as a V1 affordability proxy, not as an exact travel price.

Input:

- `data/raw/destination_costs.csv`

Features:

| Feature | Rule | Reason |
| --- | --- | --- |
| `cost_of_living_index` | Numeric affordability proxy | Gives the recommender a comparable cost signal. |
| `cost_level` | `<45 = Budget`, `45-65 = Mid-range`, `>65 = Luxury` | Turns the numeric proxy into a user-facing category. |

The recommendation engine compares the user's selected budget with
`cost_level` and creates a `budget_match_score`. This is used as a soft scoring
component, not a strict filter. In the V1 recommendation formula, budget match
has a 15% weight, enough to change rankings while still allowing strong
destination matches to remain competitive.

Terminology:

- Budget preference = what the user selects in the interface.
- Travel cost level / `cost_level` = how expensive the destination is estimated
  to be.
- `budget_match_score` = how well the budget preference and destination cost
  level match.

Current implementation note: budget support is functional in V1, but
`cost_level` is currently based mainly on the fallback `cost_of_living_index`.
The richer `travel_cost_index` is prepared for V2 and requires live Numbeo and
Amadeus API credentials.

The V1 budget match is intentionally gradual:

| User budget preference | Budget destination | Mid-range destination | Luxury destination |
| --- | ---: | ---: | ---: |
| Low (Essential) | 100 | 65 | 25 |
| Medium (Comfort) | 75 | 100 | 70 |
| High (Luxury) | 60 | 85 | 100 |

This avoids penalizing otherwise strong destinations too aggressively while the
cost feature is still based on a proxy.

## Travel Cost Features V2

For the advanced version, Smart Travel can replace the simple
`cost_of_living_index` proxy with a richer `travel_cost_index`.

Script:

- `src/collect_travel_costs.py`

Output:

- `data/processed/destinations_travel_costs.csv`

Planned/collected components:

| Feature | Source idea | Reason |
| --- | --- | --- |
| `median_hotel_price_eur` | Hotel pricing API near destination coordinates | Accommodation is usually the largest travel cost. |
| `restaurant_meal_price_eur` | Numbeo city prices | Captures eating-out cost. |
| `cappuccino_price_eur` | Numbeo city prices | Captures cafe cost. |
| `groceries_basket_price_eur` | Numbeo city prices | Helps budget-oriented travelers. |
| `museum_or_attraction_price_eur` | Attractions API or future source | Captures activity cost when available. |
| `local_transport_price_eur` | Numbeo city prices | Captures local mobility cost. |
| `travel_cost_index` | Weighted score across components | More realistic travel affordability feature. |
| `travel_cost_level` | Budget, Mid-range, Luxury | User-facing cost label. |
| `cost_data_coverage` | Share of available cost components | Makes missing cost data explicit. |

If `destinations_travel_costs.csv` exists, `feature_engineering.py` uses
`travel_cost_level` as the main `cost_level`. If not, it falls back to the V1
cost-of-living proxy.

## Notes For Modeling

These features are designed to support:

- K-Means clustering
- explainable recommendations
- user preference matching
- future API responses

For clustering, boolean and categorical columns should be encoded before
training. Numeric score and intensity columns should be scaled before K-Means.

For recommendations, the most useful features are likely:

- `food_score`
- `nightlife_score`
- `culture_score`
- `nature_score`
- `beach_score`
- `overall_score`
- `dominant_travel_style`
- `climate_category`
- `summer_destination`
- `rain_risk`
- `cost_of_living_index`
- `cost_level`

## Clustering Model Comparison

K-Means is not the only possible clustering algorithm. The project includes an
additional comparison script:

- `src/compare_clustering_algorithms.py`

Output:

- `data/processed/clustering_algorithm_comparison.csv`

The script compares:

- K-Means for `k=2`, `k=3`, and `k=4`;
- Hierarchical clustering for `k=2`, `k=3`, and `k=4`;
- DBSCAN with several `eps` values.

This comparison is useful because the best statistical metric is not always the
best product choice. For example, DBSCAN can produce a high silhouette score by
marking many destinations as noise. That is not very useful for Smart Travel,
because every destination still needs an interpretable profile.

K-Means remains the preferred V1 model because:

- the selected features are numeric;
- the data is standardized before clustering;
- the resulting clusters are easy to summarize with feature averages;
- the cluster labels can be translated into travel profiles;
- every destination receives exactly one profile.

Limitations:

- K-Means assumes roughly compact clusters;
- it is sensitive to outliers;
- the number of clusters must be chosen manually;
- with only 20 destinations, metrics should be interpreted carefully.
