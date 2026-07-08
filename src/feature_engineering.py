import pandas as pd


INPUT_PATH = "data/processed/destinations_with_places.csv"
OUTPUT_PATH = "data/processed/destinations_feature_engineered.csv"
COST_INPUT_PATH = "data/raw/destination_costs.csv"
TRAVEL_COST_INPUT_PATH = "data/processed/destinations_travel_costs.csv"

SCORE_COLUMNS = [
    "food_score",
    "nightlife_score",
    "culture_score",
    "nature_score",
    "beach_score",
]

PLACE_COUNT_COLUMNS = [
    "restaurant_count",
    "cafe_count",
    "bar_count",
    "museum_count",
    "park_count",
    "nearby_beach_count",
]

ISLAND_DESTINATIONS = {
    "Kefalonia",
    "Mallorca",
    "Sardinia",
    "Santorini",
}

MOUNTAIN_DESTINATIONS = {
    "Interlaken",
    "Zermatt",
    "Lake Bled",
}

COASTAL_DESTINATIONS = {
    "Kefalonia",
    "Santorini",
    "Funchal",
    "Mallorca",
    "Sardinia",
    "Dubrovnik",
    "Split",
    "Nice",
    "Amalfi",
    "Cinque Terre",
    "Amsterdam",
}


def min_max_score(series):
    min_value = series.min()
    max_value = series.max()

    if max_value == min_value:
        return pd.Series(0, index=series.index)

    return ((series - min_value) / (max_value - min_value) * 100).round(2)


def cost_level_from_index(cost_index):
    if cost_index < 45:
        return "Budget"
    if cost_index <= 65:
        return "Mid-range"
    return "Luxury"


def climate_category(row):
    if row["summer_avg_temp"] >= 24 and row["winter_avg_temp"] >= 10:
        return "Warm"

    if row["summer_avg_temp"] < 22 or row["winter_avg_temp"] < 2:
        return "Cool"

    return "Mild"


def travel_style(row):
    scores = {
        "Beach": row["beach_score"],
        "Nature": row["nature_score"],
        "Culture": row["culture_score"],
        "Food & Nightlife": (row["food_score"] + row["nightlife_score"]) / 2,
    }

    sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best_style, best_score = sorted_scores[0]
    second_best_score = sorted_scores[1][1]

    if best_score - second_best_score <= 10:
        return "Balanced"

    return best_style


def add_climate_features(df):
    engineered = df.copy()

    engineered["warm_destination"] = engineered["summer_avg_temp"] >= 24
    engineered["cold_destination"] = engineered["winter_avg_temp"] < 5
    engineered["summer_destination"] = (
        (engineered["summer_avg_temp"] >= 24)
        & (engineered["summer_avg_daily_rain"] <= 1.5)
    )
    engineered["winter_destination"] = engineered["winter_avg_temp"] < 5
    engineered["rain_risk"] = engineered[
        [
            "winter_avg_daily_rain",
            "spring_avg_daily_rain",
            "summer_avg_daily_rain",
            "autumn_avg_daily_rain",
        ]
    ].max(axis=1) > 3
    engineered["climate_category"] = engineered.apply(climate_category, axis=1)

    return engineered


def add_destination_type_features(df):
    engineered = df.copy()

    if "destination_type" in engineered.columns:
        destination_type = engineered["destination_type"].fillna("city")
        engineered["island_destination"] = destination_type.eq("island")
        engineered["mountain_destination"] = destination_type.eq("mountain")
        engineered["coastal_destination"] = destination_type.isin(
            ["coastal_city", "island", "region"]
        )
    else:
        engineered["island_destination"] = engineered["destination_name"].isin(
            ISLAND_DESTINATIONS
        )
        engineered["mountain_destination"] = engineered["destination_name"].isin(
            MOUNTAIN_DESTINATIONS
        )
        engineered["coastal_destination"] = engineered["destination_name"].isin(
            COASTAL_DESTINATIONS
        )
    engineered["city_destination"] = (
        engineered[["restaurant_count", "cafe_count", "bar_count", "museum_count"]]
        .sum(axis=1)
        .rank(pct=True)
        >= 0.6
    )

    return engineered


def add_experience_features(df):
    engineered = df.copy()

    engineered["food_scene_intensity"] = min_max_score(
        engineered["restaurant_count"] + engineered["cafe_count"]
    )
    engineered["nightlife_intensity"] = min_max_score(engineered["bar_count"])
    engineered["cultural_density"] = min_max_score(engineered["museum_count"])
    engineered["nature_density"] = min_max_score(
        engineered["park_count"] + engineered["nearby_beach_count"]
    )

    engineered["overall_score"] = engineered[SCORE_COLUMNS].mean(axis=1).round(2)
    engineered["score_balance_std"] = engineered[SCORE_COLUMNS].std(axis=1).round(2)
    engineered["balanced_destination"] = engineered["score_balance_std"] <= 15
    engineered["dominant_travel_style"] = engineered.apply(travel_style, axis=1)

    return engineered


def add_cost_features(df):
    engineered = df.copy()

    try:
        travel_costs = pd.read_csv(TRAVEL_COST_INPUT_PATH)
        travel_cost_columns = [
            "destination_name",
            "country",
            "month",
            "avg_hotel_price_eur",
            "median_hotel_price_eur",
            "hotel_sample_size",
            "restaurant_meal_price_eur",
            "cappuccino_price_eur",
            "groceries_basket_price_eur",
            "museum_or_attraction_price_eur",
            "local_transport_price_eur",
            "travel_cost_index",
            "travel_cost_level",
            "cost_data_coverage",
        ]
        available_columns = [
            column for column in travel_cost_columns if column in travel_costs.columns
        ]
        engineered = engineered.merge(
            travel_costs[available_columns],
            on=["destination_name", "country"],
            how="left",
            validate="one_to_one",
        )
    except FileNotFoundError:
        pass

    try:
        costs = pd.read_csv(COST_INPUT_PATH)
    except FileNotFoundError:
        if "cost_level" not in engineered.columns:
            engineered["cost_level"] = "Unknown"
        return engineered

    engineered = engineered.merge(
        costs,
        on=["destination_name", "country"],
        how="left",
        validate="one_to_one",
    )
    engineered["cost_of_living_level"] = engineered["cost_of_living_index"].apply(
        lambda value: "Unknown" if pd.isna(value) else cost_level_from_index(value)
    )
    if "travel_cost_level" in engineered.columns:
        has_travel_cost_data = (
            engineered["travel_cost_level"].notna()
            & engineered["travel_cost_level"].ne("Unknown")
        )
        if "cost_data_coverage" in engineered.columns:
            has_travel_cost_data = has_travel_cost_data & (
                engineered["cost_data_coverage"].fillna(0) > 0
            )
        engineered["cost_level"] = engineered["cost_of_living_level"]
        engineered.loc[has_travel_cost_data, "cost_level"] = engineered.loc[
            has_travel_cost_data, "travel_cost_level"
        ]
    else:
        engineered["cost_level"] = engineered["cost_of_living_level"]

    return engineered


def build_feature_engineered_dataset(df):
    engineered = add_climate_features(df)
    engineered = add_destination_type_features(engineered)
    engineered = add_experience_features(engineered)
    engineered = add_cost_features(engineered)

    return engineered


def main():
    destinations = pd.read_csv(INPUT_PATH)
    engineered = build_feature_engineered_dataset(destinations)
    engineered.to_csv(OUTPUT_PATH, index=False)

    new_columns = [
        column
        for column in engineered.columns
        if column not in destinations.columns
    ]

    print("Done!")
    print(f"Created {len(new_columns)} engineered features:")
    print(new_columns)
    print(engineered[["destination_name", *new_columns]].head())


if __name__ == "__main__":
    main()
