# Smart Travel TODO

This file separates what is implemented from what is planned, so the project
does not confuse visual UI elements with fully supported data features.

## Implemented

- Natural travel-planner UI in Streamlit.
- Preference translation layer:
  - `src/preference_translation.py`
  - keeps translation rules in dictionaries through `PREFERENCE_TRANSLATION_RULES`;
  - converts trip style, companion, activities, preferred weather, and free text
    into internal numeric signals:
    - `food`
    - `beach`
    - `culture`
    - `nature`
    - `nightlife`
  - travel companion is part of the scoring logic, not only UI:
    - Solo: `culture +2`, `food +1`
    - Partner: `beach +2`, `food +2`, `nightlife +1`
    - Friends: `nightlife +3`, `food +2`
    - Family: `nature +2`, `culture +1`, `nightlife -2`
  - preferred weather is part of the scoring logic:
    - Warm: comfort curve centered around `27C`
    - Mild: comfort curve centered around `21C`
    - Cool: comfort curve centered around `15C`
    - Any: uses a general comfort temperature inferred from trip intent.
  - free-text input uses lightweight keyword extraction:
    - activity keywords adjust food/beach/culture/nature/nightlife;
    - weather keywords can infer Warm/Mild/Cool when weather is set to Any.
    - synonyms and small typos are handled with simple fuzzy matching.
- Content-based recommendation engine:
  - `src/recommend.py`
  - uses translated preference signals, weather score, budget match score,
    cluster bonus, and must-have penalties.
- Budget support V1:
  - uses `cost_of_living_index` as an affordability proxy;
  - derives `cost_level`;
  - compares the user's budget preference with the destination's `cost_level`;
  - creates `budget_match_score`;
  - exposes `cost_score` as the cost component of the recommendation formula;
  - contributes 15% to the final recommendation score.
- Travel cost pipeline scaffold V2:
  - `src/collect_travel_costs.py`
  - ready for Numbeo and Amadeus API keys;
  - outputs `destinations_travel_costs.csv` when real API data is available.

## Partially Implemented / Needs Real Data

- Budget V2:
  - the advanced script exists, but real travel-cost data requires API keys:
    - `NUMBEO_API_KEY`
    - `AMADEUS_CLIENT_ID`
    - `AMADEUS_CLIENT_SECRET`
  - until `data/processed/destinations_travel_costs.csv` exists with real
    coverage, the project falls back to `cost_of_living_index`.
  - TODO: Replace the fallback `cost_of_living_index` with a real
    `travel_cost_index` once Numbeo and Amadeus API keys are available.
  - V2: replace `cost_of_living_index` proxy with `travel_cost_index` based on
    hotel, restaurant, transport, grocery, cafe, and attraction prices.
- Attraction and museum prices:
  - placeholder exists as `museum_or_attraction_price_eur`;
  - a reliable source still needs to be selected.
- Hotel prices:
  - Amadeus integration is scaffolded;
  - needs credentials and live API validation.
- Free-text interpretation:
  - implemented with lightweight keyword extraction;
  - handles synonyms and small typos with simple fuzzy matching;
  - future version can replace this with NLP or an LLM.

## Planned

- Collect monthly travel costs instead of a single representative month.
- Replace fallback cost-of-living proxy with full `travel_cost_index`.
- Add cost coverage warnings in the dashboard when travel-cost data is missing.
- Expand destination guides for all destinations, not only the most common
  recommendations.
- Add automated tests for:
  - preference translation;
  - budget matching;
  - recommendation output schema;
  - travel-cost fallback behavior.
- Add notebook visualizations for clustering comparison:
  - K-Means vs Hierarchical vs DBSCAN;
  - cluster profiles;
  - limitations and final model choice.
