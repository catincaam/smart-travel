import time

import pandas as pd
import requests


OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
SEARCH_RADIUS_METERS = 3000
REQUEST_DELAY_SECONDS = 2
REQUEST_TIMEOUT_SECONDS = 45

INPUT_PATH = "data/processed/destinations_enriched_weather.csv"
OUTPUT_PATH = "data/processed/destinations_with_places.csv"
PARTIAL_OUTPUT_PATH = "data/processed/places_partial.csv"

PLACE_FEATURES = {
    "restaurant_count": ("amenity", "restaurant"),
    "cafe_count": ("amenity", "cafe"),
    "bar_count": ("amenity", "bar"),
    "museum_count": ("tourism", "museum"),
    "park_count": ("leisure", "park"),
    "nearby_beach_count": ("natural", "beach"),
}

SCORE_FEATURES = {
    "food_score": ["restaurant_count", "cafe_count"],
    "nightlife_score": ["bar_count"],
    "culture_score": ["museum_count"],
    "nature_score": ["park_count"],
    "beach_score": ["nearby_beach_count"],
}

DESTINATION_TYPE_RADIUS_METERS = {
    "city": 3000,
    "coastal_city": 8000,
    "mountain": 5000,
    "island": 15000,
    "region": 15000,
}

DESTINATION_TYPE_OVERRIDES = {
    "Kefalonia": "island",
    "Santorini": "island",
    "Funchal": "island",
    "Mallorca": "island",
    "Sardinia": "island",
    "Dubrovnik": "coastal_city",
    "Split": "coastal_city",
    "Lisbon": "coastal_city",
    "Barcelona": "coastal_city",
    "Nice": "coastal_city",
    "Amalfi": "coastal_city",
    "Cinque Terre": "region",
    "Interlaken": "mountain",
    "Zermatt": "mountain",
    "Lake Bled": "mountain",
}


def destination_type_for(row):
    destination_type = row.get("destination_type")

    if isinstance(destination_type, str) and destination_type:
        return destination_type

    return DESTINATION_TYPE_OVERRIDES.get(row["destination_name"], "city")


def search_radius_for(destination_type):
    return DESTINATION_TYPE_RADIUS_METERS.get(
        destination_type,
        SEARCH_RADIUS_METERS,
    )


def get_osm_count(latitude, longitude, tag_key, tag_value, radius=SEARCH_RADIUS_METERS):
    query = f"""
    [out:json][timeout:25];
    (
      node["{tag_key}"="{tag_value}"](around:{radius},{latitude},{longitude});
      way["{tag_key}"="{tag_value}"](around:{radius},{latitude},{longitude});
      relation["{tag_key}"="{tag_value}"](around:{radius},{latitude},{longitude});
    );
    out count;
    """

    for url in OVERPASS_URLS:
        try:
            response = requests.post(
                url,
                data={"data": query},
                headers={"User-Agent": "smart-travel-project"},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()
            return int(data["elements"][0]["tags"]["total"])
        except Exception as error:
            print(
                f"Could not collect {tag_key}={tag_value} "
                f"for {latitude}, {longitude} from {url}: {error}",
                flush=True,
            )

    return None


def get_osm_counts(latitude, longitude, place_features, radius=SEARCH_RADIUS_METERS):
    query_parts = ["[out:json][timeout:35];"]

    for _, (tag_key, tag_value) in place_features.items():
        query_parts.extend(
            [
                f'node["{tag_key}"="{tag_value}"](around:{radius},{latitude},{longitude});',
                "out count;",
                f'way["{tag_key}"="{tag_value}"](around:{radius},{latitude},{longitude});',
                "out count;",
                f'relation["{tag_key}"="{tag_value}"](around:{radius},{latitude},{longitude});',
                "out count;",
            ]
        )

    query = "\n".join(query_parts)

    for url in OVERPASS_URLS:
        try:
            response = requests.post(
                url,
                data={"data": query},
                headers={"User-Agent": "smart-travel-project"},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()

            counts = {}
            elements = data["elements"]
            for index, output_column in enumerate(place_features):
                feature_counts = elements[index * 3 : index * 3 + 3]
                counts[output_column] = sum(
                    int(element["tags"]["total"]) for element in feature_counts
                )

            return counts
        except Exception as error:
            print(
                f"Could not collect batched places for "
                f"{latitude}, {longitude} from {url}: {error}",
                flush=True,
            )

    return {output_column: None for output_column in place_features}


def collect_place_features(row):
    destination_type = destination_type_for(row)
    search_radius_m = search_radius_for(destination_type)
    result = {
        "destination_name": row["destination_name"],
        "country": row["country"],
        "destination_type": destination_type,
        "search_radius_m": search_radius_m,
        "place_latitude": row["latitude"],
        "place_longitude": row["longitude"],
    }

    print(
        f"Collecting places for {row['destination_name']} "
        f"({destination_type}, radius={search_radius_m}m)...",
        flush=True,
    )
    result.update(
        get_osm_counts(
            row["latitude"],
            row["longitude"],
            PLACE_FEATURES,
            radius=search_radius_m,
        )
    )
    time.sleep(REQUEST_DELAY_SECONDS)

    return result


def has_complete_current_result(existing_result, row):
    if not existing_result:
        return False

    if any(pd.isna(existing_result[column]) for column in PLACE_FEATURES):
        return False

    if "place_latitude" not in existing_result or "place_longitude" not in existing_result:
        return False

    destination_type = destination_type_for(row)
    search_radius_m = search_radius_for(destination_type)
    if existing_result.get("destination_type") != destination_type:
        return False

    if int(existing_result.get("search_radius_m", 0)) != search_radius_m:
        return False

    return (
        round(float(existing_result["place_latitude"]), 4) == round(float(row["latitude"]), 4)
        and round(float(existing_result["place_longitude"]), 4)
        == round(float(row["longitude"]), 4)
    )


def add_scores(destinations_with_places):
    scored_destinations = destinations_with_places.copy()

    for score_column, count_columns in SCORE_FEATURES.items():
        raw_score = scored_destinations[count_columns].sum(axis=1, min_count=1)
        max_score = raw_score.max()

        if pd.isna(max_score) or max_score == 0:
            scored_destinations[score_column] = 0
        else:
            scored_destinations[score_column] = (
                (raw_score / max_score) * 100
            ).round(2)

    return scored_destinations


def main():
    destinations = pd.read_csv(INPUT_PATH)
    results_by_destination = {}

    try:
        partial_df = pd.read_csv(PARTIAL_OUTPUT_PATH)
        for _, row in partial_df.iterrows():
            key = (row["destination_name"], row["country"])
            results_by_destination[key] = row.to_dict()
    except FileNotFoundError:
        pass

    for _, row in destinations.iterrows():
        key = (row["destination_name"], row["country"])
        existing_result = results_by_destination.get(key)

        if has_complete_current_result(existing_result, row):
            print(f"Skipping completed {row['destination_name']}...", flush=True)
        else:
            results_by_destination[key] = collect_place_features(row)

        partial_df = pd.DataFrame(results_by_destination.values())
        partial_df.to_csv(PARTIAL_OUTPUT_PATH, index=False)

    places_df = pd.DataFrame(results_by_destination.values()).drop(
        columns=["place_latitude", "place_longitude"],
        errors="ignore",
    )
    if "destination_type" in destinations.columns:
        places_df = places_df.drop(columns=["destination_type"], errors="ignore")

    destinations_with_places = destinations.merge(
        places_df,
        on=["destination_name", "country"],
        how="left",
    )
    destinations_with_places = add_scores(destinations_with_places)
    destinations_with_places.to_csv(OUTPUT_PATH, index=False)

    print("Done!", flush=True)
    print(destinations_with_places.head(), flush=True)


if __name__ == "__main__":
    main()
