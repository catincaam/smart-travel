import argparse
import math
from pathlib import Path

import pandas as pd


INPUT_PATH = Path("data/processed/destinations_clustered.csv")
FEATURE_ENGINEERED_PATH = Path("data/processed/destinations_feature_engineered.csv")
OUTPUT_PATH = Path("data/processed/recommendation_sample.csv")

PREFERENCE_COLUMNS = {
    "food": "food_recommendation_signal",
    "nightlife": "nightlife_recommendation_signal",
    "culture": "culture_recommendation_signal",
    "nature": "nature_recommendation_signal",
    "beach": "beach_recommendation_signal",
}

BUDGET_TO_COST_SCORE = {
    "Low (Essential)": 1,
    "Medium (Comfort)": 2,
    "High (Luxury)": 3,
}

BUDGET_MATCH_MATRIX = {
    "Low (Essential)": {
        "Budget": 100,
        "Mid-range": 65,
        "Luxury": 25,
    },
    "Medium (Comfort)": {
        "Budget": 75,
        "Mid-range": 100,
        "Luxury": 70,
    },
    "High (Luxury)": {
        "Budget": 60,
        "Mid-range": 85,
        "Luxury": 100,
    },
}

MONTH_TO_SEASON = {
    "january": "winter",
    "february": "winter",
    "march": "spring",
    "april": "spring",
    "may": "spring",
    "june": "summer",
    "july": "summer",
    "august": "summer",
    "september": "autumn",
    "october": "autumn",
    "november": "autumn",
    "december": "winter",
}

WEATHER_COMFORT_PROFILES = {
    "warm": {"ideal_temp": 27, "tolerance": 5},
    "mild": {"ideal_temp": 21, "tolerance": 4},
    "cool": {"ideal_temp": 15, "tolerance": 4},
}


def clamp(value, minimum=0, maximum=100):
    return max(minimum, min(maximum, value))


def load_destinations():
    """Load clustered destinations and make sure all recommendation scores exist."""
    clustered = normalize_beach_columns(pd.read_csv(INPUT_PATH))

    required_scores = set(PREFERENCE_COLUMNS.values())
    required_features = {
        "cost_of_living_index",
        "cost_level",
        "dominant_travel_style",
        "climate_category",
    }
    if required_scores.issubset(clustered.columns) and required_features.issubset(
        clustered.columns
    ):
        return add_recommendation_signals(clustered)

    # The clustering output can be narrow. For recommendations, we merge clusters
    # back into the full feature-engineered dataset so no scoring columns are lost.
    full_dataset = normalize_beach_columns(pd.read_csv(FEATURE_ENGINEERED_PATH))
    cluster_columns = clustered[["destination_name", "country", "cluster", "cluster_profile"]]
    merged = full_dataset.merge(
        cluster_columns,
        on=["destination_name", "country"],
        how="left",
        validate="one_to_one",
    )
    merged = normalize_beach_columns(merged)
    merged.to_csv(INPUT_PATH, index=False)
    return add_recommendation_signals(merged)


def normalize_beach_columns(df):
    """Support both the old and the clearer V1 beach column names."""
    normalized = df.copy()

    if "nearby_beach_count" not in normalized.columns and "beach_count" in normalized.columns:
        normalized = normalized.rename(columns={"beach_count": "nearby_beach_count"})

    for suffix_column in ["nearby_beach_count_x", "nearby_beach_count_y"]:
        if "nearby_beach_count" not in normalized.columns and suffix_column in normalized.columns:
            normalized["nearby_beach_count"] = normalized[suffix_column]

    return normalized


def percentile_score(series):
    return (series.rank(pct=True) * 100).round(2)


def add_recommendation_signals(df):
    """Create robust ranking signals for recommendations.

    The user-facing scores are useful for EDA, but they are min-max scores and can
    be dominated by very large cities. For recommendations, percentile signals
    make the ranking more stable for a small dataset.
    """
    recommendations = normalize_beach_columns(df)

    if "nearby_beach_count" not in recommendations.columns:
        available_columns = ", ".join(recommendations.columns)
        raise KeyError(
            "Missing nearby_beach_count. Re-run collect_places.py and "
            f"feature_engineering.py. Available columns: {available_columns}"
        )

    recommendations["food_recommendation_signal"] = percentile_score(
        recommendations["restaurant_count"] + recommendations["cafe_count"]
    )
    recommendations["nightlife_recommendation_signal"] = percentile_score(
        recommendations["bar_count"]
    )
    recommendations["culture_recommendation_signal"] = percentile_score(
        recommendations["museum_count"]
    )
    recommendations["nature_recommendation_signal"] = percentile_score(
        recommendations["park_count"] + recommendations["nearby_beach_count"]
    )
    recommendations["beach_recommendation_signal"] = percentile_score(
        recommendations["nearby_beach_count"]
    )

    return recommendations


def normalize_preferences(preferences):
    total = sum(preferences.values())

    if total == 0:
        equal_weight = 1 / len(preferences)
        return {key: equal_weight for key in preferences}

    return {key: value / total for key, value in preferences.items()}


def season_from_month(month):
    normalized_month = month.strip().lower()

    if normalized_month not in MONTH_TO_SEASON:
        valid_months = ", ".join(month.title() for month in MONTH_TO_SEASON)
        raise ValueError(f"Invalid month '{month}'. Use one of: {valid_months}.")

    return MONTH_TO_SEASON[normalized_month]


def calculate_weather_score(row, season, beach_preference):
    temp = row[f"{season}_avg_temp"]
    rain = row[f"{season}_avg_daily_rain"]

    # Backwards-compatible default: if the user does not express a weather
    # preference, infer a comfortable temperature from the trip intent.
    ideal_temp = 27 if beach_preference >= 7 else 22

    temp_score = clamp(100 - (abs(temp - ideal_temp) / 12 * 100))
    rain_score = clamp(100 - (rain * 20))

    return round((0.7 * temp_score) + (0.3 * rain_score), 2)


def temperature_comfort_score(temp, ideal_temp, tolerance):
    distance = (temp - ideal_temp) / tolerance
    return round(math.exp(-0.5 * (distance**2)) * 100, 2)


def calculate_weather_preference_score(row, season, weather_preference, beach_preference):
    temp = row[f"{season}_avg_temp"]
    rain = row[f"{season}_avg_daily_rain"]
    normalized_preference = weather_preference.strip().lower()

    if normalized_preference not in WEATHER_COMFORT_PROFILES:
        return calculate_weather_score(row, season, beach_preference)

    profile = WEATHER_COMFORT_PROFILES[normalized_preference]
    temp_score = temperature_comfort_score(
        temp,
        profile["ideal_temp"],
        profile["tolerance"],
    )
    rain_score = clamp(100 - (rain * 20))
    return round((0.75 * temp_score) + (0.25 * rain_score), 2)


def calculate_budget_match_score(row, budget):
    cost_level = row.get("cost_level", "Mid-range")
    budget_scores = BUDGET_MATCH_MATRIX.get(
        budget,
        BUDGET_MATCH_MATRIX["Medium (Comfort)"],
    )

    return budget_scores.get(cost_level, 70)


def calculate_cluster_bonus(row, preferences):
    profile = row.get("cluster_profile", "")

    if profile == "Warm Coastal & Beach" and preferences["beach"] >= 7:
        return 5

    urban_average = (
        preferences["food"] + preferences["culture"] + preferences["nightlife"]
    ) / 3
    if profile == "Urban Culture & Food" and urban_average >= 7:
        return 5

    if profile == "Cool Balanced & Nature" and preferences["nature"] >= 7:
        return 5

    return 0


def calculate_must_have_penalty(row, preferences):
    """Penalize destinations that miss a preference the user marked as important."""
    penalty = 0

    for preference_name, score_column in PREFERENCE_COLUMNS.items():
        preference_value = preferences[preference_name]
        destination_score = row[score_column]

        if preference_value < 7 or destination_score >= 40:
            continue

        missing_strength = (40 - destination_score) / 40
        preference_strength = preference_value / 10
        penalty += 30 * missing_strength * preference_strength

    profile = row.get("cluster_profile", "")
    if preferences["beach"] >= 7 and profile != "Warm Coastal & Beach":
        penalty += 8

    if preferences["nature"] >= 7 and profile == "Urban Culture & Food":
        penalty += 6

    return round(penalty, 2)


def build_explanation(row, preferences, season):
    reasons = []

    for preference_name, score_column in PREFERENCE_COLUMNS.items():
        if preferences[preference_name] >= 7 and row[score_column] >= 60:
            readable_name = preference_name.replace("_", " ")
            reasons.append(f"strong {readable_name} match")

    if row["weather_score"] >= 75:
        temp = row[f"{season}_avg_temp"]
        rain = row[f"{season}_avg_daily_rain"]
        reasons.append(f"good {season} weather ({temp:.1f}C, {rain:.1f} mm rain/day)")

    if pd.notna(row.get("cluster_profile")):
        reasons.append(f"belongs to {row['cluster_profile']}")

    if not reasons:
        reasons.append("balanced match across the selected preferences")

    return "; ".join(reasons[:4])


def build_reason(row):
    return {
        "weather": round(row["weather_score"], 2),
        "budget": round(row["budget_match_score"], 2),
        "food": round(row["food_recommendation_signal"], 2),
        "beach": round(row["beach_recommendation_signal"], 2),
        "culture": round(row["culture_recommendation_signal"], 2),
        "nature": round(row["nature_recommendation_signal"], 2),
        "nightlife": round(row["nightlife_recommendation_signal"], 2),
        "cluster_bonus": round(row["cluster_bonus"], 2),
        "must_have_penalty": round(row["must_have_penalty"], 2),
    }


def build_natural_reason(row, preferences, season, budget):
    main_preferences = [
        preference_name
        for preference_name, preference_value in preferences.items()
        if preference_value >= 7
    ]
    readable_preferences = " and ".join(main_preferences)

    if not readable_preferences:
        readable_preferences = "your selected preferences"

    strengths = []
    if row["weather_score"] >= 75:
        strengths.append("good seasonal weather")
    if row["food_recommendation_signal"] >= 60:
        strengths.append("a strong food scene")
    if row["beach_recommendation_signal"] >= 60:
        strengths.append("strong beach availability")
    if row["nature_recommendation_signal"] >= 60:
        strengths.append("good nature access")
    if row["culture_recommendation_signal"] >= 60:
        strengths.append("strong cultural attractions")
    if row["nightlife_recommendation_signal"] >= 60:
        strengths.append("good nightlife")
    if row["budget_match_score"] >= 80:
        strengths.append(f"a {row.get('cost_level', 'balanced')} cost profile")

    if not strengths:
        strengths.append("a balanced profile across the selected criteria")

    strengths_text = ", ".join(strengths[:3])
    return (
        f"{row['destination_name']} was recommended because it matches "
        f"{readable_preferences}, with {strengths_text}, and belongs to the "
        f"{row['cluster_profile']} profile for {season} travel."
    )


def recommend_destinations(
    preferences,
    travel_month="August",
    top_n=5,
    budget="Medium (Comfort)",
    weather_preference="Any",
):
    destinations = load_destinations()
    season = season_from_month(travel_month)
    weights = normalize_preferences(preferences)

    recommendations = destinations.copy()

    recommendations["preference_score"] = 0
    for preference_name, score_column in PREFERENCE_COLUMNS.items():
        recommendations["preference_score"] += (
            recommendations[score_column] * weights[preference_name]
        )

    recommendations["weather_score"] = recommendations.apply(
        lambda row: calculate_weather_preference_score(
            row,
            season,
            weather_preference,
            preferences["beach"],
        ),
        axis=1,
    )
    recommendations["budget_match_score"] = recommendations.apply(
        lambda row: calculate_budget_match_score(row, budget),
        axis=1,
    )
    recommendations["cost_score"] = recommendations["budget_match_score"]
    recommendations["cluster_bonus"] = recommendations.apply(
        lambda row: calculate_cluster_bonus(row, preferences),
        axis=1,
    )
    recommendations["must_have_penalty"] = recommendations.apply(
        lambda row: calculate_must_have_penalty(row, preferences),
        axis=1,
    )
    recommendations["recommendation_score"] = (
        (0.60 * recommendations["preference_score"])
        + (0.20 * recommendations["weather_score"])
        + (0.15 * recommendations["cost_score"])
        + recommendations["cluster_bonus"]
        - recommendations["must_have_penalty"]
    ).round(2)
    recommendations["recommendation_score"] = recommendations[
        "recommendation_score"
    ].clip(upper=100)
    recommendations["explanation"] = recommendations.apply(
        lambda row: build_explanation(row, preferences, season),
        axis=1,
    )
    recommendations["reason"] = recommendations.apply(build_reason, axis=1)
    recommendations["natural_reason"] = recommendations.apply(
        lambda row: build_natural_reason(row, preferences, season, budget),
        axis=1,
    )

    output_columns = [
        "destination_name",
        "country",
        "recommendation_score",
        "preference_score",
        "weather_score",
        "cost_score",
        "budget_match_score",
        "cost_of_living_index",
        "cost_level",
        "cluster_profile",
        "dominant_travel_style",
        "climate_category",
        "summer_avg_temp",
        "summer_avg_daily_rain",
        "search_radius_m",
        "restaurant_count",
        "museum_count",
        "nearby_beach_count",
        "explanation",
        "natural_reason",
        "reason",
    ]

    return (
        recommendations[output_columns]
        .sort_values("recommendation_score", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Recommend Smart Travel destinations.")
    parser.add_argument("--food", type=float, default=8, help="Food preference, 0-10.")
    parser.add_argument("--beach", type=float, default=9, help="Beach preference, 0-10.")
    parser.add_argument("--culture", type=float, default=3, help="Culture preference, 0-10.")
    parser.add_argument("--nature", type=float, default=6, help="Nature preference, 0-10.")
    parser.add_argument(
        "--nightlife", type=float, default=4, help="Nightlife preference, 0-10."
    )
    parser.add_argument("--month", default="August", help="Travel month.")
    parser.add_argument(
        "--budget",
        default="Medium (Comfort)",
        choices=list(BUDGET_TO_COST_SCORE),
        help="Budget preference.",
    )
    parser.add_argument(
        "--weather-preference",
        default="Any",
        choices=["Warm", "Mild", "Cool", "Any"],
        help="Preferred weather for the selected travel month.",
    )
    parser.add_argument("--top-n", type=int, default=5, help="Number of results.")

    return parser.parse_args()


def main():
    args = parse_args()
    preferences = {
        "food": args.food,
        "beach": args.beach,
        "culture": args.culture,
        "nature": args.nature,
        "nightlife": args.nightlife,
    }

    recommendations = recommend_destinations(
        preferences=preferences,
        travel_month=args.month,
        top_n=args.top_n,
        budget=args.budget,
        weather_preference=args.weather_preference,
    )
    recommendations.to_csv(OUTPUT_PATH, index=False)

    print("Recommendation Engine V1")
    print(f"Travel month: {args.month}")
    print(f"Budget: {args.budget}")
    print(f"Weather preference: {args.weather_preference}")
    print("Preferences:", preferences)
    print()
    print(recommendations.to_string(index=False))
    print()
    print(f"Saved sample recommendations to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
