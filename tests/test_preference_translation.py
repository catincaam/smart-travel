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


import pytest


@pytest.mark.parametrize('text,excluded', [
    ('no beach', 'beach'), ('without nightlife', 'nightlife'),
    ("I don't want clubs", 'nightlife'), ('avoid museums', 'culture'),
    ('fără plajă', 'beach'), ('no beches', 'beach'),
])
def test_simple_negation_overrides_default_and_activity_weights(text, excluded):
    preferences = translate_user_preferences('Balanced Trip', ['Beach', 'Nightlife', 'Museums'], 'Friends', 'Any', text)
    assert preferences[excluded] == 0
    assert excluded in extract_text_signals(text)['excluded_preferences']


def test_negation_scope_preserves_positive_clause():
    signals = extract_text_signals('no nightlife, but museums and local food')
    assert signals['excluded_preferences'] == ['nightlife']
    assert signals['preference_weights']['culture'] == 3
    assert signals['preference_weights']['food'] == 3


def test_not_only_is_not_an_exclusion():
    assert extract_text_signals('not only museums but also food')['excluded_preferences'] == []


@pytest.mark.parametrize('text,expected', [
    ('not too hot', 'Mild'), ('no hot weather', 'Any'),
    ('not cold, but warm', 'Warm'), ('warm or cool', 'Any'),
])
def test_weather_negation_and_ambiguous_intent(text, expected):
    assert infer_weather_preference('Any', text) == expected
