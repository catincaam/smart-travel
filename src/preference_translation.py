import re
import unicodedata
from difflib import SequenceMatcher


TRIP_STYLES = {
    "Beach Holiday": {
        "food": 6,
        "beach": 10,
        "culture": 2,
        "nature": 5,
        "nightlife": 2,
    },
    "City Break": {
        "food": 7,
        "beach": 1,
        "culture": 9,
        "nature": 3,
        "nightlife": 6,
    },
    "Nature & Hiking": {
        "food": 4,
        "beach": 3,
        "culture": 3,
        "nature": 10,
        "nightlife": 1,
    },
    "Food & Wine": {
        "food": 10,
        "beach": 2,
        "culture": 5,
        "nature": 3,
        "nightlife": 4,
    },
    "Nightlife With Friends": {
        "food": 7,
        "beach": 3,
        "culture": 3,
        "nature": 2,
        "nightlife": 10,
    },
    "Balanced Trip": {
        "food": 6,
        "beach": 6,
        "culture": 6,
        "nature": 6,
        "nightlife": 4,
    },
}

ACTIVITY_WEIGHTS = {
    "Beach": {"beach": 3},
    "Local food": {"food": 3},
    "Museums": {"culture": 3},
    "Nature": {"nature": 3},
    "Wine": {"food": 2, "culture": 1},
    "Nightlife": {"nightlife": 3, "food": 1},
    "Hiking": {"nature": 3},
    "Photography": {"culture": 1, "nature": 2},
}

TRAVEL_COMPANION_WEIGHTS = {
    "Solo": {"culture": 2, "food": 1},
    "Partner": {"beach": 2, "food": 2, "nightlife": 1},
    "Friends": {"nightlife": 3, "food": 2},
    "Family": {"nature": 2, "culture": 1, "nightlife": -2},
}

KEYWORD_WEIGHTS = {
    "beach": {
        "terms": ["beach", "beaches", "plaja", "plaje", "sea", "seaside", "coast", "coastal", "swim", "swimming"],
        "weights": {"beach": 3},
    },
    "food": {
        "terms": ["food", "restaurant", "restaurants", "local food", "cuisine", "dining", "eat", "eating", "wine"],
        "weights": {"food": 3},
    },
    "culture": {
        "terms": ["museum", "museums", "history", "historic", "culture", "architecture", "old town", "monuments"],
        "weights": {"culture": 3},
    },
    "nature": {
        "terms": [
            "nature",
            "hike",
            "hiking",
            "trek",
            "trekking",
            "trail",
            "trails",
            "mountain",
            "mountains",
            "lake",
            "parks",
            "scenic",
            "landscape",
            "outdoors",
        ],
        "weights": {"nature": 3},
    },
    "nightlife": {
        "terms": ["nightlife", "party", "club", "clubs", "bar", "bars", "friends"],
        "weights": {"nightlife": 3},
    },
    "relax": {
        "terms": ["relax", "relaxing", "quiet", "peaceful", "romantic", "chill", "slow"],
        "weights": {"beach": 1, "nature": 1},
    },
}

TEXT_WEATHER_KEYWORDS = {
    "Warm": ["warm", "hot", "sunny", "sun", "summer", "heat", "beach weather"],
    "Mild": [
        "mild",
        "moderate",
        "pleasant",
        "walkable",
        "not too hot",
        "good weather",
        "nice weather",
        "weather good",
        "good enough",
    ],
    "Cool": ["cool", "cold", "chilly", "fresh", "snow", "winter"],
}

WEATHER_OPTIONS = ["Warm", "Mild", "Cool", "Any"]

PREFERENCE_TRANSLATION_RULES = {
    "trip_styles": TRIP_STYLES,
    "activities": ACTIVITY_WEIGHTS,
    "travel_companions": TRAVEL_COMPANION_WEIGHTS,
    "text_keywords": KEYWORD_WEIGHTS,
    "text_weather_keywords": TEXT_WEATHER_KEYWORDS,
    "weather_options": WEATHER_OPTIONS,
}


def clamp_preference(value):
    return max(0, min(10, int(round(value))))


def apply_weights(preferences, weights):
    updated = preferences.copy()
    for key, value in weights.items():
        updated[key] = clamp_preference(updated.get(key, 0) + value)
    return updated


def text_contains_term(text, term):
    if " " in term:
        return term in text
    return re.search(rf"\b{re.escape(term)}\b", text) is not None


def tokenize_text(text):
    return re.findall(r"[a-zA-Z]+", text)


def fuzzy_contains_term(tokens, term):
    if " " in term or len(term) < 4:
        return False

    return any(SequenceMatcher(None, token, term).ratio() >= 0.84 for token in tokens)


def text_matches_any_term(text, tokens, terms):
    return any(
        text_contains_term(text, term) or fuzzy_contains_term(tokens, term)
        for term in terms
    )


def normalize_text(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text.lower().replace("’", "'")) if not unicodedata.combining(c))


def term_polarities(text, terms):
    """Recognize short negated clauses; do not claim general language understanding."""
    polarities = set()
    clauses = re.split(r"[.,;!?]|\b(?:but|however|with|dar|insa|cu)\b|\band (?=i |we |want |prefer )", text)
    for clause in clauses:
        tokens = tokenize_text(clause)
        for term in terms:
            term_tokens = term.split()
            for index in range(len(tokens) - len(term_tokens) + 1):
                candidate = tokens[index:index + len(term_tokens)]
                exact = candidate == term_tokens
                fuzzy = len(term_tokens) == 1 and len(term) >= 4 and SequenceMatcher(None, candidate[0], term).ratio() >= 0.84
                if not (exact or fuzzy):
                    continue
                prefix = " ".join(tokens[:index])
                prefix = re.sub(r"\bnot (?:only|just)\b", "", prefix)
                negative = bool(re.search(r"\b(?:no|not|without|avoid|exclude|skip|fara|nu|don t|donot)\b", prefix))
                polarities.add(-1 if negative else 1)
    return polarities


def extract_text_signals(trip_description):
    text = normalize_text(trip_description)
    preference_weights = {}
    matched_keywords = []
    excluded_preferences = set()
    for keyword, config in KEYWORD_WEIGHTS.items():
        polarities = term_polarities(text, config["terms"])
        if -1 in polarities:
            # Explicit opt-outs take precedence over default style/activity weights.
            if keyword in ("beach", "food", "culture", "nature", "nightlife"):
                excluded_preferences.update(config["weights"])
        elif 1 in polarities:
            matched_keywords.append(keyword)
            for preference, value in config["weights"].items():
                preference_weights[preference] = preference_weights.get(preference, 0) + value

    weather_votes = {
        label: sum(1 for term in terms if 1 in term_polarities(text, [term]))
        for label, terms in TEXT_WEATHER_KEYWORDS.items()
    }
    # This common phrase expresses mild weather, not a desire for heat.
    if re.search(r"\bnot (?:too )?hot\b", text):
        weather_votes["Mild"] += 2
    highest = max(weather_votes.values())
    winners = [label for label, votes in weather_votes.items() if votes == highest]
    inferred_weather = winners[0] if highest and len(winners) == 1 else None
    return {
        "preference_weights": preference_weights,
        "weather_preference": inferred_weather,
        "matched_keywords": matched_keywords,
        "excluded_preferences": sorted(excluded_preferences),
    }


def apply_text_matching(preferences, trip_description):
    signals = extract_text_signals(trip_description)
    updated = preferences.copy()

    updated = apply_weights(updated, signals["preference_weights"])
    for preference in signals["excluded_preferences"]:
        updated[preference] = 0

    return updated


def translate_user_preferences(
    trip_style,
    activities,
    companion,
    climate_preference,
    trip_description,
):
    """Translate natural travel-planner answers into recommender signals."""
    preferences = TRIP_STYLES[trip_style].copy()
    preferences = apply_weights(preferences, TRAVEL_COMPANION_WEIGHTS[companion])

    for activity in activities:
        preferences = apply_weights(preferences, ACTIVITY_WEIGHTS[activity])

    # Weather preference is handled separately by the recommender's weather_score.
    # It should not directly change food/beach/culture/nature/nightlife intent.
    preferences = apply_text_matching(preferences, trip_description)
    return {key: clamp_preference(value) for key, value in preferences.items()}


def infer_weather_preference(climate_preference, trip_description):
    if climate_preference != "Any":
        return climate_preference

    text_weather_preference = extract_text_signals(trip_description)["weather_preference"]
    return text_weather_preference or climate_preference


build_preferences = translate_user_preferences
