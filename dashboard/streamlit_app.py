from pathlib import Path
import sys
import base64
import mimetypes

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
MAP_PATH = PROJECT_ROOT / "maps" / "smart_travel_map.html"
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "destinations_clustered.csv"
DESTINATION_ASSETS_PATH = PROJECT_ROOT / "dashboard" / "assets" / "destinations"

sys.path.append(str(SRC_PATH))

from recommend import recommend_destinations  # noqa: E402
from preference_translation import (  # noqa: E402
    ACTIVITY_WEIGHTS,
    TRAVEL_COMPANION_WEIGHTS,
    TRIP_STYLES,
    WEATHER_OPTIONS,
    infer_weather_preference,
    translate_user_preferences,
)


MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

DESTINATION_IMAGES = {
    "Nice": "https://images.unsplash.com/photo-1533105079780-92b9be482077?auto=format&fit=crop&w=900&q=80",
    "Mallorca": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=900&q=80",
    "Split": "https://images.unsplash.com/photo-1555993539-1732b0258235?auto=format&fit=crop&w=900&q=80",
    "Barcelona": "https://images.unsplash.com/photo-1583422409516-2895a77efded?auto=format&fit=crop&w=900&q=80",
    "Kefalonia": "https://images.unsplash.com/photo-1601581875309-fafbf2d3ed3a?auto=format&fit=crop&w=900&q=80",
    "Santorini": "https://images.unsplash.com/photo-1570077188670-e3a8d69ac5ff?auto=format&fit=crop&w=900&q=80",
    "Paris": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=900&q=80",
    "Prague": "https://images.unsplash.com/photo-1541849546-216549ae216d?auto=format&fit=crop&w=900&q=80",
    "Vienna": "https://images.unsplash.com/photo-1516550893923-42d28e5677af?auto=format&fit=crop&w=900&q=80",
    "Amsterdam": "https://images.unsplash.com/photo-1534351590666-13e3e96b5017?auto=format&fit=crop&w=900&q=80",
    "Lisbon": "https://images.unsplash.com/photo-1501927023255-9063be98970c?auto=format&fit=crop&w=900&q=80",
}

LOCAL_DESTINATION_IMAGES = {
    "Dubrovnik": "dubrovnik.jpg",
    "Mallorca": "mallorca.jpg",
    "Nice": "nice.jpg",
    "Sardinia": "sardinia.jpg",
    "Split": "split.jpg",
}

CLUSTER_IMAGES = {
    "Warm Coastal & Beach": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=900&q=80",
    "Urban Culture & Food": "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=900&q=80",
    "Cool Balanced & Nature": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=900&q=80",
}

FRIENDLY_CLUSTER_LABELS = {
    "Warm Coastal & Beach": "Warm Coastal Escape",
    "Urban Culture & Food": "Culture & Food City",
    "Cool Balanced & Nature": "Nature Retreat",
}

DESTINATION_GUIDES = {
    "Mallorca": {
        "airport": "Palma de Mallorca Airport",
        "stay": "5-7 days",
        "best_months": "May, June, September",
        "dont_miss": ["Palma Cathedral", "Valldemossa", "Soller", "Cap de Formentor", "Cala d'Or"],
        "highlights": ["Clear coastal coves", "Scenic villages", "Mediterranean food", "Easy day trips"],
        "good_to_know": ["Budget: medium", "Crowds: high in August", "Driving: recommended"],
    },
    "Nice": {
        "airport": "Nice Cote d'Azur Airport",
        "stay": "3-5 days",
        "best_months": "May, June, September",
        "dont_miss": ["Promenade des Anglais", "Old Nice", "Castle Hill", "Cours Saleya", "Villefranche-sur-Mer"],
        "highlights": ["Beach promenade", "Excellent food scene", "Easy Riviera day trips", "Warm weather"],
        "good_to_know": ["Budget: medium-high", "Crowds: high in summer", "Transport: strong train links"],
    },
    "Split": {
        "airport": "Split Airport",
        "stay": "4-6 days",
        "best_months": "May, June, September",
        "dont_miss": ["Diocletian's Palace", "Marjan Hill", "Riva promenade", "Hvar day trip", "Trogir"],
        "highlights": ["Historic old town", "Island day trips", "Coastal walks", "Lively food scene"],
        "good_to_know": ["Budget: medium", "Crowds: high in July-August", "Ferries: very useful"],
    },
    "Lisbon": {
        "airport": "Humberto Delgado Airport",
        "stay": "4-6 days",
        "best_months": "April, May, September",
        "dont_miss": ["Alfama", "Belem Tower", "LX Factory", "Sintra day trip", "Time Out Market"],
        "highlights": ["Food and cafes", "Viewpoints", "Historic neighborhoods", "Coastal day trips"],
        "good_to_know": ["Budget: medium", "Hills: expect walking", "Transport: metro and trams"],
    },
    "Cinque Terre": {
        "airport": "Pisa International Airport",
        "stay": "3-4 days",
        "best_months": "May, June, September",
        "dont_miss": ["Monterosso", "Vernazza", "Manarola", "Corniglia", "Coastal hiking trails"],
        "highlights": ["Colorful villages", "Coastal hiking", "Sea views", "Local seafood"],
        "good_to_know": ["Budget: medium", "Crowds: high mid-summer", "Transport: use the train"],
    },
    "Kefalonia": {
        "airport": "Kefalonia International Airport",
        "stay": "5-7 days",
        "best_months": "June, September",
        "dont_miss": ["Myrtos Beach", "Assos", "Fiskardo", "Melissani Cave", "Antisamos Beach"],
        "highlights": ["Relaxed beaches", "Scenic villages", "Clear water", "Nature drives"],
        "good_to_know": ["Budget: medium", "Driving: recommended", "Pace: relaxed"],
    },
    "Sardinia": {
        "airport": "Cagliari Elmas Airport",
        "stay": "7-10 days",
        "best_months": "June, September",
        "dont_miss": ["Cagliari", "Costa Smeralda", "La Maddalena", "Alghero", "Cala Gonone"],
        "highlights": ["Dramatic coastline", "Nature access", "Regional food", "Road trips"],
        "good_to_know": ["Budget: medium-high", "Driving: recommended", "Distances: plan carefully"],
    },
    "Barcelona": {
        "airport": "Barcelona-El Prat Airport",
        "stay": "4-6 days",
        "best_months": "April, May, September",
        "dont_miss": ["Sagrada Familia", "Gothic Quarter", "Park Guell", "Barceloneta", "Casa Batllo"],
        "highlights": ["Architecture", "Food and nightlife", "Urban beach", "Museums"],
        "good_to_know": ["Budget: medium-high", "Crowds: high", "Transport: excellent metro"],
    },
    "Paris": {
        "airport": "Charles de Gaulle Airport",
        "stay": "4-7 days",
        "best_months": "April, May, September",
        "dont_miss": ["Louvre", "Eiffel Tower", "Montmartre", "Seine walk", "Le Marais"],
        "highlights": ["Museums", "Food scene", "Iconic neighborhoods", "Walkability"],
        "good_to_know": ["Budget: high", "Book museums ahead", "Transport: excellent metro"],
    },
    "Amsterdam": {
        "airport": "Amsterdam Schiphol Airport",
        "stay": "3-5 days",
        "best_months": "April, May, September",
        "dont_miss": ["Canal Ring", "Rijksmuseum", "Jordaan", "Anne Frank House", "Vondelpark"],
        "highlights": ["Canals", "Museums", "Cycling", "Compact city center"],
        "good_to_know": ["Budget: high", "Book popular museums ahead", "Transport: bike and tram"],
    },
}


st.set_page_config(
    page_title="Smart Travel Dashboard",
    layout="wide",
)

st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #fffaf8 0%, #fbf7f5 100%);
        border-right: 1px solid #f0ded8;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #6b5751;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #2b2421;
    }
    [data-testid="stSidebar"] button[kind="primary"] {
        background: #fff3ef;
        border: 1.5px solid #c72512;
        color: #c72512;
        border-radius: 12px;
        font-weight: 700;
        box-shadow: 0 8px 18px rgba(199, 37, 18, 0.08);
    }
    [data-testid="stSidebar"] button[kind="secondary"] {
        background: #fffdfc;
        border: 1px solid #ead8d1;
        color: #433633;
        border-radius: 12px;
    }
    .planner-brand {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 4px 0 14px 0;
        border-bottom: 1px solid #f1dfd9;
        margin-bottom: 22px;
    }
    .planner-logo {
        color: #c72512;
        font-size: 20px;
        font-weight: 800;
    }
    .planner-avatar {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background: linear-gradient(135deg, #f7c6b8, #fff3ef);
        border: 1px solid #ead8d1;
    }
    .planner-title {
        font-size: 24px;
        font-weight: 800;
        color: #292321;
        margin-bottom: 8px;
    }
    .planner-copy {
        color: #7b6962;
        font-size: 14px;
        line-height: 1.5;
        margin-bottom: 24px;
    }
    .sidebar-label {
        color: #6f5b55;
        font-size: 14px;
        font-weight: 600;
        margin: 18px 0 8px 0;
    }
    .hero-card {
        min-height: 260px;
        padding: 30px 28px;
        border-radius: 22px;
        background:
            linear-gradient(135deg, rgba(255,255,255,0.92), rgba(255,255,255,0.68)),
            url("https://images.unsplash.com/photo-1521295121783-8a321d551ad2?auto=format&fit=crop&w=1400&q=75");
        background-size: cover;
        background-position: center;
        border: 1px solid #f1dfd9;
        box-shadow: 0 16px 35px rgba(80, 45, 30, 0.08);
        margin-bottom: 24px;
    }
    .hero-pill {
        display: inline-flex;
        padding: 5px 10px;
        border-radius: 999px;
        background: #fff3ee;
        color: #c72512;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.04em;
        margin-bottom: 18px;
    }
    .hero-title {
        font-size: 40px;
        line-height: 1.05;
        font-weight: 800;
        color: #171312;
        margin-bottom: 18px;
        max-width: 560px;
    }
    .hero-copy {
        color: #5f4f49;
        max-width: 560px;
        font-size: 16px;
        line-height: 1.6;
    }
    .stat-card {
        background: #fffdfc;
        border: 1px solid #f0dfd9;
        border-radius: 16px;
        padding: 20px;
        min-height: 112px;
        box-shadow: 0 14px 26px rgba(70, 43, 33, 0.06);
    }
    .stat-value {
        font-size: 30px;
        font-weight: 800;
        color: #2b2421;
        margin-top: 8px;
    }
    .stat-label {
        color: #6b5751;
        font-size: 13px;
        font-weight: 600;
    }
    .section-heading {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin: 24px 0 12px 0;
    }
    .section-heading h2 {
        margin: 0;
        font-size: 26px;
        color: #15110f;
    }
    .section-link {
        color: #c72512;
        font-weight: 700;
        font-size: 14px;
    }
    .destination-card {
        display: grid;
        grid-template-columns: minmax(260px, 35%) minmax(0, 1fr);
        height: 330px;
        overflow: hidden;
        border-radius: 22px;
        background: #fffdfc;
        border: 1px solid #f0dfd9;
        box-shadow: 0 18px 40px rgba(70, 43, 33, 0.10);
        margin-bottom: 26px;
    }
    .destination-image-wrap {
        position: relative;
        height: 330px;
        overflow: hidden;
        background: #f5eee9;
    }
    .destination-image {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center;
        display: block;
    }
    .destination-photo {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }
    .destination-image-gradient {
        position: absolute;
        inset: 0;
        background: linear-gradient(180deg, rgba(0,0,0,0.02) 35%, rgba(0,0,0,0.58) 100%);
    }
    .destination-image-overlay {
        position: absolute;
        left: 22px;
        right: 22px;
        bottom: 20px;
        color: #fff;
        text-shadow: 0 2px 12px rgba(0,0,0,0.35);
    }
    .destination-image-name {
        font-size: 24px;
        font-weight: 850;
        line-height: 1.1;
    }
    .destination-image-country {
        font-size: 13px;
        font-weight: 700;
        opacity: 0.92;
        margin-top: 4px;
    }
    .rating-badge {
        position: absolute;
        top: 16px;
        right: 16px;
        background: rgba(255,255,255,0.94);
        color: #2e241f;
        border-radius: 999px;
        padding: 7px 12px;
        font-weight: 800;
        font-size: 14px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
    }
    .destination-body {
        display: flex;
        flex-direction: column;
        justify-content: center;
        min-width: 0;
        padding: 24px 30px;
    }
    .destination-topline {
        display: flex;
        justify-content: space-between;
        gap: 18px;
        align-items: flex-start;
    }
    .destination-title {
        font-size: 24px;
        font-weight: 850;
        color: #15110f;
        margin: 0;
    }
    .destination-subtitle {
        color: #7a3427;
        font-size: 14px;
        font-weight: 600;
        margin-top: 4px;
    }
    .match-ring {
        width: 76px;
        height: 76px;
        border-radius: 50%;
        background:
            radial-gradient(circle at center, #fff 55%, transparent 57%),
            conic-gradient(#ff5a45 var(--pct), #f2e2dc 0);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        color: #2e241f;
        flex: 0 0 auto;
    }
    .match-ring span {
        line-height: 1;
    }
    .match-ring small {
        color: #84675f;
        font-size: 10px;
        font-weight: 800;
        margin-top: 4px;
        text-transform: uppercase;
    }
    .destination-reason {
        color: #533f38;
        font-size: 14px;
        line-height: 1.55;
        margin: 14px 0 14px 0;
        max-width: 820px;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .destination-facts {
        display: grid;
        grid-template-columns: repeat(5, minmax(116px, 1fr));
        gap: 8px;
        margin: 16px 0 12px 0;
    }
    .fact-pill {
        background: #fffaf7;
        border: 1px solid #f3d8cf;
        border-radius: 14px;
        padding: 10px 11px;
        min-height: 76px;
    }
    .fact-value {
        color: #1f1916;
        font-size: 14px;
        font-weight: 850;
        line-height: 1.1;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .fact-label {
        color: #80675f;
        font-size: 11px;
        font-weight: 700;
        margin-top: 4px;
    }
    .fact-meta {
        color: #a48a82;
        font-size: 10px;
        font-weight: 700;
        margin-top: 3px;
    }
    .signal-excellent {
        background: #f0fbf5;
        border-color: #bfe8cf;
    }
    .signal-high {
        background: #f2f7ff;
        border-color: #c8dcff;
    }
    .signal-moderate {
        background: #fff8e6;
        border-color: #f1d89a;
    }
    .signal-limited,
    .signal-low {
        background: #f8f7f6;
        border-color: #ded7d2;
    }
    .tag-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 0;
    }
    .travel-tag {
        color: #c72512;
        background: #fff1ed;
        border: 1px solid #ffd8cf;
        border-radius: 999px;
        padding: 7px 11px;
        font-size: 12px;
        font-weight: 800;
    }
    @media (max-width: 900px) {
        .destination-card {
            grid-template-columns: 1fr;
            height: auto;
        }
        .destination-image-wrap {
            height: 260px;
        }
        .destination-body {
            padding: 26px 24px;
        }
        .destination-facts {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }
    .concierge-card {
        border: 1px solid #4e67df;
        background: linear-gradient(135deg, #fff7f4, #f5f7ff);
        border-radius: 20px;
        padding: 22px;
        margin: 26px 0;
    }
    .concierge-title {
        font-weight: 850;
        font-size: 18px;
        color: #2b2421;
    }
    .concierge-copy {
        color: #6b5751;
        font-size: 14px;
        margin-top: 4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_destinations(data_mtime):
    return normalize_beach_columns(pd.read_csv(DATA_PATH))


def normalize_beach_columns(df):
    normalized = df.copy()
    if "nearby_beach_count" not in normalized.columns and "beach_count" in normalized.columns:
        normalized = normalized.rename(columns={"beach_count": "nearby_beach_count"})
    return normalized


def enrich_recommendations_with_facts(recommendations, destinations):
    recommendations = normalize_beach_columns(recommendations)
    destinations = normalize_beach_columns(destinations)

    fact_columns = [
        "destination_name",
        "country",
        "summer_avg_temp",
        "summer_avg_daily_rain",
        "search_radius_m",
        "restaurant_count",
        "museum_count",
        "nearby_beach_count",
    ]
    available_fact_columns = [
        column for column in fact_columns if column in destinations.columns
    ]
    missing_fact_columns = [
        column
        for column in fact_columns
        if column not in recommendations.columns
    ]

    if not missing_fact_columns:
        return recommendations

    destination_facts = destinations[available_fact_columns].drop_duplicates(
        subset=["destination_name", "country"]
    )
    return recommendations.merge(
        destination_facts,
        on=["destination_name", "country"],
        how="left",
    )


def initialize_planner_state():
    defaults = {
        "trip_style": "Nature & Hiking",
        "companion": "Partner",
        "budget": "Medium (Comfort)",
        "climate_preference": "Mild",
        "activities": ["Museums", "Photography"],
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if st.session_state.trip_style not in TRIP_STYLES:
        st.session_state.trip_style = defaults["trip_style"]
    if st.session_state.companion not in TRAVEL_COMPANION_WEIGHTS:
        st.session_state.companion = defaults["companion"]
    if st.session_state.climate_preference not in WEATHER_OPTIONS:
        st.session_state.climate_preference = defaults["climate_preference"]
    st.session_state.activities = [
        activity
        for activity in st.session_state.activities
        if activity in ACTIVITY_WEIGHTS
    ]


def sidebar_label(text):
    st.markdown(f'<div class="sidebar-label">{text}</div>', unsafe_allow_html=True)


def select_button(label, state_key, value, disabled=False):
    selected = st.session_state[state_key] == value
    st.button(
        label,
        key=f"{state_key}_{value}",
        type="primary" if selected else "secondary",
        disabled=disabled,
        use_container_width=True,
        on_click=set_session_value,
        args=(state_key, value),
    )


def set_session_value(state_key, value):
    st.session_state[state_key] = value


def toggle_activity(activity):
    current = list(st.session_state.activities)
    if activity in current:
        current.remove(activity)
    else:
        current.append(activity)
    st.session_state.activities = current


def render_trip_style_cards():
    trip_styles = list(TRIP_STYLES.keys())
    for index in range(0, len(trip_styles), 2):
        cols = st.columns(2)
        for col, style in zip(cols, trip_styles[index : index + 2]):
            with col:
                select_button(style, "trip_style", style)


def render_segmented_options(label, state_key, options, disabled_options=None, columns_per_row=None):
    disabled_options = disabled_options or set()
    columns_per_row = columns_per_row or len(options)
    sidebar_label(label)
    for index in range(0, len(options), columns_per_row):
        cols = st.columns(columns_per_row)
        for col, option in zip(cols, options[index : index + columns_per_row]):
            with col:
                select_button(option, state_key, option, disabled=option in disabled_options)


def render_activity_chips():
    sidebar_label("Must-do activities")
    activities = list(ACTIVITY_WEIGHTS.keys())
    for index in range(0, len(activities), 2):
        cols = st.columns(2)
        for col, activity in zip(cols, activities[index : index + 2]):
            with col:
                selected = activity in st.session_state.activities
                st.button(
                    activity,
                    key=f"activity_{activity}",
                    type="primary" if selected else "secondary",
                    use_container_width=True,
                    on_click=toggle_activity,
                    args=(activity,),
                )


def format_score(score):
    return f"{score:.1f}/100"


@st.cache_data
def local_image_data_url(filename):
    image_path = DESTINATION_ASSETS_PATH / filename

    if not image_path.exists():
        return None

    mime_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def destination_image(row):
    local_filename = LOCAL_DESTINATION_IMAGES.get(row["destination_name"])
    if local_filename:
        local_image_url = local_image_data_url(local_filename)
        if local_image_url:
            return local_image_url

    return DESTINATION_IMAGES.get(
        row["destination_name"],
        CLUSTER_IMAGES.get(row["cluster_profile"], CLUSTER_IMAGES["Warm Coastal & Beach"]),
    )


def fallback_destination_image(row):
    return CLUSTER_IMAGES.get(row["cluster_profile"], CLUSTER_IMAGES["Warm Coastal & Beach"])


def friendly_cluster_profile(row):
    return FRIENDLY_CLUSTER_LABELS.get(row["cluster_profile"], row["cluster_profile"])


def destination_rating(row):
    return 4.0 + (row["recommendation_score"] / 100)


def tag_from_reason(row):
    reason = row["reason"]
    tags = []

    if reason["beach"] >= 80:
        tags.append("Excellent beaches")
    elif reason["beach"] >= 60:
        tags.append("Beach friendly")

    if reason["food"] >= 80:
        tags.append("Amazing food")
    elif reason["food"] >= 60:
        tags.append("Great food")

    if reason["weather"] >= 80:
        tags.append("Excellent weather")
    elif reason["weather"] >= 60:
        tags.append("Good weather")

    if reason["nature"] >= 80:
        tags.append("Nature escapes")
    elif reason["culture"] >= 80:
        tags.append("Culture rich")
    elif reason["nightlife"] >= 80:
        tags.append("Nightlife")

    return tags[:3] or ["Balanced match"]


def beach_access_level(nearby_beach_count):
    """Turn raw OSM beach features into a user-friendly travel signal."""
    if nearby_beach_count >= 60:
        return "Excellent"
    if nearby_beach_count >= 21:
        return "High"
    if nearby_beach_count >= 6:
        return "Moderate"
    return "Low"


def score_level(score):
    if score >= 80:
        return "Excellent"
    if score >= 60:
        return "High"
    if score >= 35:
        return "Moderate"
    return "Limited"


def weather_level(row):
    reason = row.get("reason", {})
    weather_score = reason.get("weather", 0)
    if weather_score >= 80:
        return "Excellent"
    if weather_score >= 60:
        return "Good"
    if weather_score >= 35:
        return "Mixed"
    return "Limited"


def budget_level(row):
    budget_score = row.get("reason", {}).get("budget", 0)
    if budget_score >= 80:
        return "Excellent"
    if budget_score >= 50:
        return "Good"
    return "Limited"


def signal_class(level):
    normalized = level.lower()
    if normalized == "good":
        normalized = "high"
    if normalized == "mixed":
        normalized = "moderate"
    return f"signal-{normalized}"


def radius_label(search_radius_m):
    if pd.isna(search_radius_m) or search_radius_m <= 0:
        return "adaptive radius"

    radius_km = search_radius_m / 1000
    if radius_km.is_integer():
        return f"within {int(radius_km)} km"
    return f"within {radius_km:.1f} km"


def recommendation_facts(row):
    summer_temp = row.get("summer_avg_temp", 0)
    nearby_beach_count = row.get("nearby_beach_count", 0)
    search_radius_m = row.get("search_radius_m", 0)
    summer_rain = row.get("summer_avg_daily_rain", 0)
    reason = row.get("reason", {})

    beach_level = beach_access_level(nearby_beach_count)
    food_level = score_level(reason.get("food", 0))
    culture_level = score_level(reason.get("culture", 0))
    climate_level = weather_level(row)
    budget_fit = budget_level(row)
    cost_level = row.get("cost_level", "Unknown")

    return [
        (beach_level, "Beach access", radius_label(search_radius_m)),
        (food_level, "Food scene", "restaurants and cafes"),
        (culture_level, "Culture", "museums nearby"),
        (
            budget_fit,
            "Budget fit",
            f"Destination cost: {cost_level}<br>Cost-of-living proxy",
        ),
        (climate_level, "Summer weather", f"{summer_temp:.1f}C, {summer_rain:.1f} mm rain/day"),
    ]


def guide_for_destination(destination_name):
    return DESTINATION_GUIDES.get(
        destination_name,
        {
            "airport": "Main regional airport",
            "stay": "3-5 days",
            "best_months": "May, June, September",
            "dont_miss": ["Old town", "Local viewpoints", "Food markets", "Day trips"],
            "highlights": ["Good seasonal fit", "Balanced travel experience", "Local food", "Walkable areas"],
            "good_to_know": ["Budget: varies", "Book ahead in peak season", "Check local transport"],
        },
    )


def best_for_text(row):
    profile = row.get("cluster_profile", "")
    if profile == "Warm Coastal & Beach":
        return "Beach holidays and relaxing coastal breaks"
    if profile == "Urban Culture & Food":
        return "City breaks, food, museums, and urban exploring"
    if profile == "Cool Balanced & Nature":
        return "Nature, hiking, scenic views, and quieter escapes"
    return "Balanced trips"


def travel_story(row, companion):
    guide = guide_for_destination(row["destination_name"])
    profile_label = friendly_cluster_profile(row).lower()
    beach_level = beach_access_level(row.get("nearby_beach_count", 0)).lower()
    food_level = score_level(row.get("reason", {}).get("food", 0)).lower()
    weather = weather_level(row).lower()

    return (
        f"{row['destination_name']} is a strong choice if you want a {profile_label} "
        f"with {beach_level} beach access, a {food_level} food scene, and {weather} "
        f"seasonal weather. It works especially well for {companion.lower()} travellers "
        f"who want a trip that feels easy to plan but still has enough variety for "
        f"{guide['stay']}."
    )


def similar_destinations(row, destinations):
    if "cluster_profile" not in destinations.columns:
        return []

    similar = destinations[
        (destinations["cluster_profile"] == row["cluster_profile"])
        & (destinations["destination_name"] != row["destination_name"])
    ].copy()

    if "overall_score" in similar.columns:
        similar = similar.sort_values("overall_score", ascending=False)
    else:
        similar = similar.sort_values("destination_name")

    return similar["destination_name"].head(3).tolist()


def render_travel_story(row, destinations, companion, budget):
    guide = guide_for_destination(row["destination_name"])
    facts = recommendation_facts(row)
    similar = similar_destinations(row, destinations)

    st.subheader(f"Why you'll love {row['destination_name']}")
    st.write(travel_story(row, companion))

    glance_columns = st.columns(3)
    glance_items = [
        ("Average temperature", f"{row.get('summer_avg_temp', 0):.1f}C in summer"),
        ("Best for", best_for_text(row)),
        ("Great for", companion),
        ("Recommended stay", guide["stay"]),
        ("Budget preference", budget),
        ("Estimated cost level", row.get("cost_level", "Unknown")),
        ("Cost data basis", "Cost-of-living proxy estimate"),
        ("Closest airport", guide["airport"]),
        ("Best months", guide["best_months"]),
    ]
    for index, (label, value) in enumerate(glance_items):
        with glance_columns[index % 3]:
            st.markdown(f"**{label}**")
            st.caption(value)

    st.markdown("**Highlights**")
    st.markdown("\n".join(f"- {item}" for item in guide["highlights"]))

    st.markdown("**Things you shouldn't miss**")
    st.markdown("\n".join(f"- {item}" for item in guide["dont_miss"]))

    st.markdown("**Good to know**")
    st.markdown("\n".join(f"- {item}" for item in guide["good_to_know"]))

    st.markdown("**Why Smart Travel recommends it**")
    render_reason_scores(row["reason"])

    if similar:
        st.markdown("**Similar destinations**")
        st.caption("Based on the same K-Means destination profile.")
        st.markdown(" - ".join(similar))


def render_reason_scores(reason):
    score_columns = st.columns(3)
    visible_scores = [
        ("Weather", reason["weather"]),
        ("Food", reason["food"]),
        ("Beach", reason["beach"]),
        ("Culture", reason["culture"]),
        ("Nature", reason["nature"]),
        ("Nightlife", reason["nightlife"]),
    ]

    for index, (label, score) in enumerate(visible_scores):
        with score_columns[index % 3]:
            st.metric(label, format_score(score))
            st.progress(min(score / 100, 1.0))


def render_recommendation_card(row, rank, destinations, companion, budget):
    tags = "".join(
        f'<span class="travel-tag">{tag}</span>' for tag in tag_from_reason(row)
    )
    facts = "".join(
        f"""
        <div class="fact-pill {signal_class(level)}">
            <div class="fact-value">{level}</div>
            <div class="fact-label">{label}</div>
            <div class="fact-meta">{meta}</div>
        </div>
        """
        for level, label, meta in recommendation_facts(row)
    )
    image_url = destination_image(row)
    fallback_image_url = fallback_destination_image(row)
    profile_label = friendly_cluster_profile(row)
    rating = destination_rating(row)
    match_percent = int(round(row["recommendation_score"]))
    ring_degrees = f"{match_percent}%"

    st.markdown(
        f"""
        <div class="destination-card">
            <div class="destination-image-wrap">
                <div
                    class="destination-photo"
                    role="img"
                    aria-label="{row['destination_name']}"
                    style="background-image: url('{image_url}');"
                ></div>
                <div class="destination-image-gradient"></div>
                <div class="destination-image-overlay">
                    <div class="destination-image-name">{row['destination_name']}</div>
                    <div class="destination-image-country">{row['country']}</div>
                </div>
                <div class="rating-badge">* {rating:.1f}</div>
            </div>
            <div class="destination-body">
                <div class="destination-topline">
                    <div>
                        <h3 class="destination-title">{row['destination_name']}, {row['country']}</h3>
                        <div class="destination-subtitle">{profile_label} - {row['country']}</div>
                    </div>
                    <div class="match-ring" style="--pct: {ring_degrees};">
                        <span>{match_percent}%</span>
                        <small>AI Match</small>
                    </div>
                </div>
                <div class="destination-facts">{facts}</div>
                <div class="destination-reason">{row['natural_reason']}</div>
                <div class="tag-row">{tags}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander(f"Why {row['destination_name']}?"):
        render_travel_story(row, destinations, companion, budget)
        st.caption(
            f"Preference score: {format_score(row['preference_score'])} - "
            f"Weather score: {format_score(row['weather_score'])} - "
            f"Cost score: {format_score(row.get('cost_score', row['budget_match_score']))}"
        )


def render_map():
    if not MAP_PATH.exists():
        st.warning(
            "The interactive map has not been generated yet. "
            "Run `python src/create_interactive_map.py` first."
        )
        return

    map_html = MAP_PATH.read_text(encoding="utf-8")
    components.html(map_html, height=650, scrolling=True)


def render_hero(month, destination_count):
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-pill">AI POWERED</div>
            <div class="hero-title">Plan Your Next Trip</div>
            <div class="hero-copy">
                Discover destinations using weather, points of interest,
                geospatial data and machine learning.
            </div>
        </div>
        <div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; margin-bottom: 24px;">
            <div class="stat-card">
                <div class="stat-value">{destination_count}</div>
                <div class="stat-label">Destinations Analyzed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{month}</div>
                <div class="stat-label">Selected Month</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main():
    initialize_planner_state()
    destinations = load_destinations(DATA_PATH.stat().st_mtime)

    with st.sidebar:
        st.markdown(
            """
            <div class="planner-brand">
                <div class="planner-logo">Smart Travel</div>
                <div class="planner-avatar"></div>
            </div>
            <div class="planner-title">Plan Your Next Trip</div>
            <div class="planner-copy">
                Tell us what you are looking for, and Smart Travel will craft
                a destination shortlist for your trip.
            </div>
            """,
            unsafe_allow_html=True,
        )

        sidebar_label("When are you travelling?")
        month = st.selectbox(
            "Travel month",
            MONTHS,
            index=7,
            label_visibility="collapsed",
        )

        sidebar_label("What kind of trip are you looking for?")
        render_trip_style_cards()

        render_segmented_options(
            "Who are you travelling with?",
            "companion",
            list(TRAVEL_COMPANION_WEIGHTS.keys()),
            columns_per_row=2,
        )

        render_segmented_options(
            "Budget",
            "budget",
            ["Low (Essential)", "Medium (Comfort)", "High (Luxury)"],
            columns_per_row=1,
        )

        render_segmented_options(
            "Preferred weather",
            "climate_preference",
            WEATHER_OPTIONS,
            columns_per_row=2,
        )

        render_activity_chips()

        sidebar_label("Describe your ideal trip")
        trip_description = st.text_area(
            "Trip description",
            value="I want a warm beach destination with good food in August.",
            height=90,
            label_visibility="collapsed",
        )
        top_n = st.slider("How many recommendations?", 1, 10, 5)

    trip_style = st.session_state.trip_style
    companion = st.session_state.companion
    budget = st.session_state.budget
    climate_preference = st.session_state.climate_preference
    activities = st.session_state.activities

    preferences = translate_user_preferences(
        trip_style=trip_style,
        activities=activities,
        companion=companion,
        climate_preference=climate_preference,
        trip_description=trip_description,
    )
    effective_weather_preference = infer_weather_preference(
        climate_preference,
        trip_description,
    )

    recommendations = recommend_destinations(
        preferences=preferences,
        travel_month=month,
        top_n=top_n,
        budget=budget,
        weather_preference=effective_weather_preference,
    )
    recommendations = enrich_recommendations_with_facts(recommendations, destinations)

    render_hero(month, len(destinations))

    with st.expander("How your answers were translated"):
        st.json(
            {
                "preferences": preferences,
                "weather_preference": effective_weather_preference,
            }
        )

    st.divider()

    results_tab, map_tab, data_tab = st.tabs(["Recommendations", "Interactive Map", "Dataset"])

    with results_tab:
        st.markdown(
            """
            <div class="section-heading">
                <h2>Recommended</h2>
                <div class="section-link">View All</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for index, row in recommendations.iterrows():
            render_recommendation_card(row, index + 1, destinations, companion, budget)
        st.markdown(
            """
            <div class="concierge-card">
                <div class="concierge-title">AI Concierge Ready</div>
                <div class="concierge-copy">
                    Ask me anything about your trip to the recommended destinations.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with map_tab:
        st.header("Explore Destinations On The Map")
        st.markdown('<a id="map"></a>', unsafe_allow_html=True)
        render_map()

    with data_tab:
        st.header("Destination Dataset")
        st.dataframe(
            destinations[
                [
                    "destination_name",
                    "country",
                    "cluster_profile",
                    "dominant_travel_style",
                    "cost_level",
                    "cost_of_living_index",
                    "food_score",
                    "beach_score",
                    "culture_score",
                    "nature_score",
                    "summer_avg_temp",
                    "summer_avg_daily_rain",
                ]
            ],
            width="stretch",
        )


if __name__ == "__main__":
    main()
