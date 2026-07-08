import time

import pandas as pd
import requests


"""
This script builds the first enriched Smart Travel dataset.

Input:
    data/raw/european_destinations.csv

The raw file contains:
    destination_name -> what the user sees, e.g. "Kefalonia"
    search_name      -> what we use for accurate geocoding, e.g. "Argostoli"
    country          -> destination country
    destination_type -> city/island/region/etc., used later for POI radius rules

Pipeline:
    1. Use Nominatim/OpenStreetMap to convert search_name + country into
       latitude and longitude.
    2. Use those coordinates with Open-Meteo to collect historical daily
       weather.
    3. Aggregate daily weather into seasonal averages.
    4. Save the enriched dataset for the next pipeline step.
"""

RAW_INPUT_PATH = "data/raw/european_destinations.csv"
COORDINATES_OUTPUT_PATH = "data/processed/destinations_with_coordinates.csv"
WEATHER_OUTPUT_PATH = "data/processed/destinations_enriched_weather.csv"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
HEADERS = {"User-Agent": "smart-travel-project"}

REQUEST_DELAY_SECONDS = 1

SEASONS = {
    "winter": [12, 1, 2],
    "spring": [3, 4, 5],
    "summer": [6, 7, 8],
    "autumn": [9, 10, 11],
}


def get_coordinates(search_name, country):
    # Nominatim expects a text query such as "Argostoli, Greece".
    # It returns a list of matching places; we keep the first/best result.
    query = f"{search_name}, {country}"
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
    }

    response = requests.get(
        NOMINATIM_URL,
        params=params,
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()

    # Convert the JSON API response into normal Python dictionaries/lists.
    data = response.json()

    if not data:
        return None, None

    first_result = data[0]
    return float(first_result["lat"]), float(first_result["lon"])


def collect_coordinates(destinations):
    coordinates = []

    for _, row in destinations.iterrows():
        # search_name lets us geocode broad destinations using a precise place.
        # Example: destination_name="Kefalonia", search_name="Argostoli".
        search_name = row.get("search_name", row["destination_name"])
        print(
            f"Collecting coordinates for {row['destination_name']} "
            f"using {search_name}...",
            flush=True,
        )

        latitude, longitude = get_coordinates(search_name, row["country"])
        coordinates.append(
            {
                "destination_name": row["destination_name"],
                "search_name": search_name,
                "country": row["country"],
                "destination_type": row.get("destination_type", "city"),
                "latitude": latitude,
                "longitude": longitude,
            }
        )

        # Public APIs often rate-limit aggressive scripts. A small pause keeps
        # the pipeline polite and reduces failed requests.
        time.sleep(REQUEST_DELAY_SECONDS)

    coordinates_df = pd.DataFrame(coordinates)
    coordinates_df.to_csv(COORDINATES_OUTPUT_PATH, index=False)
    return coordinates_df


def get_seasonal_weather(latitude, longitude):
    # Open-Meteo returns daily values for the requested coordinates/date range.
    # We request the daily mean temperature and daily precipitation sum.
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": "2023-01-01",
        "end_date": "2025-12-31",
        "daily": ["temperature_2m_mean", "precipitation_sum"],
        "timezone": "auto",
    }

    response = requests.get(
        OPEN_METEO_ARCHIVE_URL,
        params=params,
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()

    # data["daily"] contains one row per day. We turn it into a DataFrame so we
    # can group/filter by month and calculate seasonal averages.
    weather = pd.DataFrame(data["daily"])
    weather["time"] = pd.to_datetime(weather["time"])
    weather["month"] = weather["time"].dt.month

    result = {}
    for season, months in SEASONS.items():
        # Example: summer uses months 6, 7, 8.
        season_data = weather[weather["month"].isin(months)]
        result[f"{season}_avg_temp"] = season_data["temperature_2m_mean"].mean()
        result[f"{season}_avg_daily_rain"] = season_data["precipitation_sum"].mean()

    return result


def collect_weather(coordinates_df):
    weather_data = []

    for _, row in coordinates_df.iterrows():
        print(f"Collecting weather for {row['destination_name']}...", flush=True)
        seasonal_weather = get_seasonal_weather(row["latitude"], row["longitude"])
        weather_data.append(
            {
                "destination_name": row["destination_name"],
                "country": row["country"],
                "destination_type": row.get("destination_type", "city"),
                **seasonal_weather,
            }
        )

        # Keep the same polite delay between weather API calls.
        time.sleep(REQUEST_DELAY_SECONDS)

    return pd.DataFrame(weather_data)


def main():
    # Step 1: load raw destination list.
    destinations = pd.read_csv(RAW_INPUT_PATH)

    # Step 2: create latitude/longitude from search_name + country.
    coordinates_df = collect_coordinates(destinations)

    # Step 3: collect and aggregate seasonal weather for each coordinate pair.
    weather_df = collect_weather(coordinates_df)

    # Step 4: combine coordinates and weather into one enriched dataset.
    destinations_enriched = coordinates_df.merge(
        weather_df,
        on=["destination_name", "country", "destination_type"],
        how="left",
    )

    # Round numeric columns to keep the CSV readable and stable.
    numeric_columns = destinations_enriched.select_dtypes(include="number").columns
    destinations_enriched[numeric_columns] = destinations_enriched[numeric_columns].round(2)
    destinations_enriched.to_csv(WEATHER_OUTPUT_PATH, index=False)

    print("Done!", flush=True)
    print(destinations_enriched.head(), flush=True)


if __name__ == "__main__":
    main()
