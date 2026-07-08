import pandas as pd

from src.recommend import (
    calculate_budget_match_score,
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
    )

    assert len(recommendations) == 3
    assert "cost_score" in recommendations.columns
    assert "budget_match_score" in recommendations.columns
    assert recommendations["recommendation_score"].between(0, 100).all()
    assert recommendations["cost_score"].equals(recommendations["budget_match_score"])
