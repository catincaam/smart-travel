import pandas as pd

from src.recommend import (
    calculate_budget_match_score,
    calculate_companion_match_score,
    recommend_destinations,
    temperature_comfort_score,
)


def test_budget_match_matrix_is_gradual():
    budget_destination = pd.Series({"cost_level": "Budget"})
    midrange_destination = pd.Series({"cost_level": "Mid-range"})
    luxury_destination = pd.Series({"cost_level": "Luxury"})

    assert calculate_budget_match_score(budget_destination, "Low (Essential)") == 100
    assert calculate_budget_match_score(midrange_destination, "Low (Essential)") == 65
    assert calculate_budget_match_score(luxury_destination, "Low (Essential)") == 25
    assert calculate_budget_match_score(luxury_destination, "High (Luxury)") == 100


def test_weather_comfort_curve_peaks_at_ideal_temperature():
    assert temperature_comfort_score(27, ideal_temp=27, tolerance=5) == 100
    assert temperature_comfort_score(24, ideal_temp=27, tolerance=5) < 100
    assert temperature_comfort_score(33, ideal_temp=27, tolerance=5) < 60


def test_recommendations_include_cost_score_and_top_n():
    preferences = {
        "food": 6,
        "beach": 6,
        "culture": 6,
        "nature": 6,
        "nightlife": 4,
    }

    recommendations = recommend_destinations(
        preferences,
        travel_month="August",
        top_n=3,
        budget="Medium (Comfort)",
        weather_preference="Warm",
        companion="Partner",
    )

    assert len(recommendations) == 3
    assert "cost_score" in recommendations.columns
    assert "budget_match_score" in recommendations.columns
    assert "companion_match_score" in recommendations.columns
    assert recommendations["recommendation_score"].between(0, 100).all()
    assert recommendations["cost_score"].equals(recommendations["budget_match_score"])


def test_companion_match_score_uses_different_travel_contexts():
    destination = pd.Series(
        {
            "food_recommendation_signal": 70,
            "beach_recommendation_signal": 90,
            "culture_recommendation_signal": 40,
            "nature_recommendation_signal": 80,
            "nightlife_recommendation_signal": 20,
            "weather_score": 85,
            "cluster_profile": "Warm Coastal & Beach",
        }
    )

    partner_score = calculate_companion_match_score(destination, "Partner")
    friends_score = calculate_companion_match_score(destination, "Friends")
    family_score = calculate_companion_match_score(destination, "Family")

    assert partner_score > friends_score
    assert family_score > friends_score


def test_zero_pois_never_receive_positive_signal():
    from src.recommend import percentile_score
    scores = percentile_score(pd.Series([0, 0, 0, 1, 10]))
    assert scores.iloc[:3].eq(0).all()
    assert scores.iloc[4] > scores.iloc[3] > 0


def test_beach_intent_favors_destinations_with_beach_access():
    result = recommend_destinations(dict(food=0, beach=10, culture=0, nature=0, nightlife=0), top_n=5)
    assert result.nearby_beach_count.gt(0).all()


def test_culture_and_nightlife_intents_produce_different_rankings():
    culture = recommend_destinations(dict(food=0, beach=0, culture=10, nature=0, nightlife=0))
    nightlife = recommend_destinations(dict(food=0, beach=0, culture=0, nature=0, nightlife=10))
    assert culture.destination_name.tolist() != nightlife.destination_name.tolist()
