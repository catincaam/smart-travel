from src.preference_translation import (
    PREFERENCE_TRANSLATION_RULES,
    extract_text_signals,
    infer_weather_preference,
    translate_user_preferences,
)


def test_translation_rules_are_configuration_driven():
    assert "trip_styles" in PREFERENCE_TRANSLATION_RULES
    assert "activities" in PREFERENCE_TRANSLATION_RULES
    assert "travel_companions" in PREFERENCE_TRANSLATION_RULES
    assert "text_keywords" in PREFERENCE_TRANSLATION_RULES


def test_travel_companion_changes_preferences():
    solo = translate_user_preferences("Balanced Trip", [], "Solo", "Any", "")
    family = translate_user_preferences("Balanced Trip", [], "Family", "Any", "")
    friends = translate_user_preferences("Balanced Trip", [], "Friends", "Any", "")

    assert solo["culture"] > friends["culture"]
    assert family["nature"] > friends["nature"]
    assert friends["nightlife"] > family["nightlife"]


def test_free_text_extracts_activity_and_weather_signals():
    signals = extract_text_signals("wether good enough to go for a hike")

    assert signals["preference_weights"]["nature"] == 3
    assert signals["weather_preference"] == "Mild"
    assert "nature" in signals["matched_keywords"]


def test_free_text_weather_only_overrides_any():
    text = "warm beach with good food"

    assert infer_weather_preference("Any", text) == "Warm"
    assert infer_weather_preference("Cool", text) == "Cool"


def test_free_text_updates_recommendation_preferences():
    preferences = translate_user_preferences(
        "Balanced Trip",
        [],
        "Solo",
        "Any",
        "warm beach with good food",
    )

    assert preferences["food"] == 10
    assert preferences["beach"] == 9
