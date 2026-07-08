import argparse
import json
import os
import statistics
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests


INPUT_PATH = Path("data/processed/destinations_with_coordinates.csv")
OUTPUT_PATH = Path("data/processed/destinations_travel_costs.csv")
CACHE_DIR = Path("data/cache/travel_costs")

NUMBEO_BASE_URL = "https://www.numbeo.com/api"
AMADEUS_AUTH_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
AMADEUS_HOTEL_LIST_URL = "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-geocode"
AMADEUS_HOTEL_OFFERS_URL = "https://test.api.amadeus.com/v3/shopping/hotel-offers"

REQUEST_DELAY_SECONDS = 1.5
DEFAULT_RADIUS_KM = 3
DEFAULT_CURRENCY = "EUR"

PRICE_ITEM_KEYWORDS = {
    "restaurant_meal_price_eur": [
        "Meal, Inexpensive Restaurant",
    ],
    "cappuccino_price_eur": [
        "Cappuccino",
    ],
    "local_transport_price_eur": [
        "One-way Ticket",
    ],
    "groceries_basket_price_eur": [
        "Loaf of Fresh White Bread",
        "Eggs",
        "Milk",
        "Apples",
        "Potato",
        "Lettuce",
    ],
}

TRAVEL_COST_WEIGHTS = {
    "hotel_price_score": 0.45,
    "restaurant_price_score": 0.20,
    "cafe_price_score": 0.10,
    "groceries_price_score": 0.10,
    "attraction_price_score": 0.10,
    "transport_price_score": 0.05,
}


def cache_path(name):
    safe_name = "".join(char if char.isalnum() or char in "-_" else "_" for char in name)
    return CACHE_DIR / f"{safe_name}.json"


def load_json_cache(name):
    path = cache_path(name)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_json_cache(name, payload):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path(name).write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def get_env(name):
    value = os.getenv(name)
    return value.strip() if isinstance(value, str) and value.strip() else None


def request_json(url, params=None, headers=None, method="GET", data=None):
    if method == "POST":
        response = requests.post(url, data=data, headers=headers, timeout=45)
    else:
        response = requests.get(url, params=params, headers=headers, timeout=45)
    response.raise_for_status()
    return response.json()


def get_numbeo_city_prices(destination_name, country, latitude, longitude, currency):
    api_key = get_env("NUMBEO_API_KEY")
    if not api_key:
        return None

    cache_key = f"numbeo_{destination_name}_{country}_{currency}"
    cached = load_json_cache(cache_key)
    if cached is not None:
        return cached

    payload = request_json(
        f"{NUMBEO_BASE_URL}/city_prices",
        params={
            "api_key": api_key,
            "query": f"{latitude},{longitude}",
            "currency": currency,
            "use_estimated": "true",
            "strict_matching": "false",
        },
    )
    save_json_cache(cache_key, payload)
    time.sleep(REQUEST_DELAY_SECONDS)
    return payload


def find_price(prices, keywords):
    matches = []
    for item in prices or []:
        item_name = item.get("item_name", "")
        if any(keyword.lower() in item_name.lower() for keyword in keywords):
            average_price = item.get("average_price")
            if average_price is not None:
                matches.append(float(average_price))
    if not matches:
        return None
    return round(statistics.mean(matches), 2)


def extract_numbeo_prices(payload):
    if not payload:
        return {
            "restaurant_meal_price_eur": None,
            "cappuccino_price_eur": None,
            "groceries_basket_price_eur": None,
            "local_transport_price_eur": None,
            "numbeo_city_name": None,
            "numbeo_contributors": None,
        }

    prices = payload.get("prices", [])
    extracted = {
        column: find_price(prices, keywords)
        for column, keywords in PRICE_ITEM_KEYWORDS.items()
    }
    extracted["numbeo_city_name"] = payload.get("name")
    extracted["numbeo_contributors"] = payload.get("contributors")
    return extracted


def amadeus_access_token():
    client_id = get_env("AMADEUS_CLIENT_ID")
    client_secret = get_env("AMADEUS_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None

    cached = load_json_cache("amadeus_token")
    if cached and cached.get("expires_at", 0) > time.time() + 60:
        return cached["access_token"]

    payload = request_json(
        AMADEUS_AUTH_URL,
        method="POST",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = payload["access_token"]
    save_json_cache(
        "amadeus_token",
        {
            "access_token": token,
            "expires_at": time.time() + int(payload.get("expires_in", 0)),
        },
    )
    return token


def get_amadeus_hotel_prices(destination_name, latitude, longitude, radius_km, currency, month):
    token = amadeus_access_token()
    if not token:
        return {
            "avg_hotel_price_eur": None,
            "median_hotel_price_eur": None,
            "hotel_sample_size": 0,
        }

    cache_key = f"amadeus_hotels_{destination_name}_{month}_{radius_km}_{currency}"
    cached = load_json_cache(cache_key)
    if cached is not None:
        return cached

    headers = {"Authorization": f"Bearer {token}"}
    hotel_list = request_json(
        AMADEUS_HOTEL_LIST_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "radius": radius_km,
            "radiusUnit": "KM",
            "hotelSource": "ALL",
        },
        headers=headers,
    )
    hotel_ids = [hotel["hotelId"] for hotel in hotel_list.get("data", [])[:20]]

    check_in = representative_check_in_date(month)
    check_out = check_in + timedelta(days=1)
    prices = []
    for hotel_id in hotel_ids:
        try:
            offers = request_json(
                AMADEUS_HOTEL_OFFERS_URL,
                params={
                    "hotelIds": hotel_id,
                    "adults": 2,
                    "checkInDate": check_in.isoformat(),
                    "checkOutDate": check_out.isoformat(),
                    "currency": currency,
                    "bestRateOnly": "true",
                },
                headers=headers,
            )
        except requests.HTTPError:
            continue

        for hotel in offers.get("data", []):
            for offer in hotel.get("offers", []):
                total = offer.get("price", {}).get("total")
                if total is not None:
                    prices.append(float(total))
        time.sleep(REQUEST_DELAY_SECONDS)

    result = {
        "avg_hotel_price_eur": round(statistics.mean(prices), 2) if prices else None,
        "median_hotel_price_eur": round(statistics.median(prices), 2) if prices else None,
        "hotel_sample_size": len(prices),
    }
    save_json_cache(cache_key, result)
    return result


def representative_check_in_date(month):
    month_number = pd.to_datetime(month, format="%B").month
    year = date.today().year + 1
    return date(year, month_number, 15)


def attraction_price_placeholder():
    return {
        "museum_or_attraction_price_eur": None,
        "attraction_price_coverage": "not_collected_v2",
    }


def min_max_cost_score(series):
    filled = series.astype(float)
    min_value = filled.min(skipna=True)
    max_value = filled.max(skipna=True)
    if pd.isna(min_value) or pd.isna(max_value) or min_value == max_value:
        return pd.Series(pd.NA, index=series.index)
    score = ((filled - min_value) / (max_value - min_value) * 100).round(2)
    score[filled.isna()] = pd.NA
    return score


def travel_cost_level(index):
    if pd.isna(index):
        return "Unknown"
    if index < 35:
        return "Budget"
    if index <= 65:
        return "Mid-range"
    return "Luxury"


def add_travel_cost_index(df):
    scored = df.copy()
    score_sources = {
        "hotel_price_score": "median_hotel_price_eur",
        "restaurant_price_score": "restaurant_meal_price_eur",
        "cafe_price_score": "cappuccino_price_eur",
        "groceries_price_score": "groceries_basket_price_eur",
        "attraction_price_score": "museum_or_attraction_price_eur",
        "transport_price_score": "local_transport_price_eur",
    }

    for score_column, source_column in score_sources.items():
        scored[score_column] = min_max_cost_score(scored[source_column])

    weighted_sum = 0
    available_weight = 0
    for score_column, weight in TRAVEL_COST_WEIGHTS.items():
        values = scored[score_column]
        available = values.notna()
        weighted_sum += values.fillna(0) * weight
        available_weight += available.astype(float) * weight

    scored["travel_cost_index"] = pd.NA
    has_cost_data = available_weight > 0
    scored.loc[has_cost_data, "travel_cost_index"] = (
        weighted_sum[has_cost_data] / available_weight[has_cost_data]
    ).round(2)
    scored["travel_cost_level"] = scored["travel_cost_index"].apply(travel_cost_level)
    scored["cost_data_coverage"] = (
        scored[
            [
                "median_hotel_price_eur",
                "restaurant_meal_price_eur",
                "cappuccino_price_eur",
                "groceries_basket_price_eur",
                "museum_or_attraction_price_eur",
                "local_transport_price_eur",
            ]
        ]
        .notna()
        .mean(axis=1)
        .round(2)
    )
    return scored


def collect_destination_cost(row, month, radius_km, currency):
    numbeo_payload = get_numbeo_city_prices(
        row["destination_name"],
        row["country"],
        row["latitude"],
        row["longitude"],
        currency,
    )
    hotel_prices = get_amadeus_hotel_prices(
        row["destination_name"],
        row["latitude"],
        row["longitude"],
        radius_km,
        currency,
        month,
    )

    return {
        "destination_name": row["destination_name"],
        "country": row["country"],
        "month": month,
        "hotel_search_radius_km": radius_km,
        **hotel_prices,
        **extract_numbeo_prices(numbeo_payload),
        **attraction_price_placeholder(),
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Collect travel cost features.")
    parser.add_argument("--month", default="August", help="Representative travel month.")
    parser.add_argument("--radius-km", type=float, default=DEFAULT_RADIUS_KM)
    parser.add_argument("--currency", default=DEFAULT_CURRENCY)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def main():
    args = parse_args()
    destinations = pd.read_csv(INPUT_PATH)
    if args.limit:
        destinations = destinations.head(args.limit)

    rows = []
    for _, row in destinations.iterrows():
        print(f"Collecting travel costs for {row['destination_name']}...", flush=True)
        rows.append(
            collect_destination_cost(
                row,
                month=args.month,
                radius_km=args.radius_km,
                currency=args.currency,
            )
        )

    costs = add_travel_cost_index(pd.DataFrame(rows))
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    costs.to_csv(OUTPUT_PATH, index=False)

    print("Done!")
    print(f"Saved travel costs to {OUTPUT_PATH}")
    print(costs.head())


if __name__ == "__main__":
    main()
