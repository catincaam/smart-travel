from pathlib import Path
import sys
import base64
import mimetypes

import pandas as pd
import streamlit as st


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
    extract_text_signals,
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
    "<style>" + (PROJECT_ROOT / "dashboard" / "styles.css").read_text() + "</style>",
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

    if reason.get("companion", 0) >= 80:
        tags.append("Great travel fit")

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
    season_temp = row["season_avg_temp"]
    nearby_beach_count = row.get("nearby_beach_count", 0)
    search_radius_m = row.get("search_radius_m", 0)
    season_rain = row["season_avg_daily_rain"]
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
        (climate_level, f"{row['travel_season'].title()} weather", f"{season_temp:.1f}°C, {season_rain:.1f} mm rain/day"),
    ]


def guide_for_destination(destination_name):
    return DESTINATION_GUIDES.get(destination_name)


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
    return (
        f"{row['natural_reason']} "
        f"Fit for your {companion.lower()} trip: {row['companion_match_score']:.0f}/100. "
        "Compare the individual scores below to see the trade-offs."
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
    similar = similar_destinations(row, destinations)

    st.subheader(f"Your match with {row['destination_name']}")
    st.write(travel_story(row, companion))

    glance_columns = st.columns(3)
    glance_items = [
        ("Average temperature", f"{row['season_avg_temp']:.1f}°C in {row['travel_season']}"),
        ("Best for", best_for_text(row)),
        ("Travel companion", companion),
        ("Budget preference", budget),
        ("Estimated cost level", row.get("cost_level", "Unknown")),
        ("Cost data basis", "Cost-of-living proxy estimate"),
    ]
    for index, (label, value) in enumerate(glance_items):
        with glance_columns[index % 3]:
            st.markdown(f"**{label}**")
            st.caption(value)

    if guide:
        st.caption("Editorial trip ideas: verify opening times, transport and availability before booking.")
        st.markdown("**Highlights**")
        st.markdown("\n".join(f"- {item}" for item in guide["highlights"]))
        st.markdown("**Places to explore**")
        st.markdown("\n".join(f"- {item}" for item in guide["dont_miss"]))
        st.markdown("**Good to know**")
        st.markdown("\n".join(f"- {item}" for item in guide["good_to_know"]))
    else:
        st.caption("A destination-specific editorial guide is not available yet. The scores below use the collected dataset.")

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
        ("Travel fit", reason["companion"]),
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
    profile_label = friendly_cluster_profile(row)
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
                <div class="rating-badge">No. {rank:02d} · Your shortlist</div>
            </div>
            <div class="destination-body">
                <div class="destination-topline">
                    <div>
                        <h3 class="destination-title">{row['destination_name']}, {row['country']}</h3>
                        <div class="destination-subtitle">{profile_label} - {row['country']}</div>
                    </div>
                    <div class="match-ring" style="--pct: {ring_degrees};">
                        <span>{match_percent}%</span>
                        <small>Match</small>
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
            f"Cost score: {format_score(row.get('cost_score', row['budget_match_score']))} - "
            f"Travel fit: {format_score(row['companion_match_score'])}"
        )


def render_map(recommendations, destinations):
    map_data = recommendations.merge(
        destinations[["destination_name", "country", "latitude", "longitude"]],
        on=["destination_name", "country"], how="left", validate="one_to_one",
    )
    located = map_data.dropna(subset=["latitude", "longitude"])
    if located.empty:
        st.info("Coordinates are unavailable for this shortlist.")
        return
    st.caption("Your current shortlist. Change the planner preferences or result count to update the map.")
    st.map(located, latitude="latitude", longitude="longitude", color="#254f40", size=15000)
    st.dataframe(
        located[["destination_name", "country", "recommendation_score", "season_avg_temp", "season_avg_daily_rain"]].rename(columns={
            "destination_name": "Destination", "country": "Country", "recommendation_score": "Match / 100",
            "season_avg_temp": "Season average °C", "season_avg_daily_rain": "Rain mm/day",
        }), hide_index=True, width="stretch",
    )


def render_hero(month, destination_count):
    hero_image = local_image_data_url("mallorca.jpg")
    st.markdown(
        f"""
        <div class="page-masthead"><span>SMART TRAVEL / THE DESTINATION EDIT</span><span>Made for your kind of escape</span></div>
        <div class="hero-card" style="background-image: linear-gradient(90deg, rgba(16,42,35,.88), rgba(16,42,35,.12)), url('{hero_image}');">
            <div class="hero-pill">A LITTLE INSPIRATION. A NEW ADVENTURE.</div>
            <h1 class="hero-title">Somewhere new.<br>Something you.</h1>
            <div class="hero-copy">Find a place that feels like your kind of trip.<br>Great food, slower days, or a little adventure — you decide.</div>
            <div class="hero-footer"><span>{destination_count} European destinations</span><span>Your {month} escape</span></div>
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
                <div class="planner-avatar" aria-hidden="true">↗</div>
            </div>
            <div class="planner-title">Your next escape</div>
            <div class="planner-copy">
                A few details about you. A world of places to discover.
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
            value="",
            placeholder="Optional: e.g. quiet walks, museums and local food",
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
        companion=companion,
    )
    recommendations = enrich_recommendations_with_facts(recommendations, destinations)

    render_hero(month, len(destinations))
    text_signals = extract_text_signals(trip_description)
    if text_signals["excluded_preferences"]:
        st.info("Interests switched off: " + ", ".join(text_signals["excluded_preferences"]) + ". These destinations may still offer those activities; this is not a hard filter.")
    st.caption("Choose your preferences in the sidebar to update your shortlist. On mobile, open the planner using the top-left arrow.")
    with st.expander("About these recommendations"):
        st.write("This prototype compares 20 European destinations. Match scores are weighted rankings, not probabilities or traveller ratings. Weather uses historical seasonal averages, not live forecasts. Budget fit uses a cost-of-living proxy, not flight or hotel quotes.")
        st.write("Trip descriptions use English keyword matching. The selected month controls the season; simple exclusions such as “no nightlife” remove that interest from preference scoring, but do not filter out destinations. Complex phrasing and dates in free text are not supported. Destination profiles come from K-Means clustering.")


    results_tab, map_tab, data_tab = st.tabs(["Recommendations", "Interactive Map", "Dataset"])

    with results_tab:
        st.markdown(
            """
            <div class="section-heading">
                <div><div class="eyebrow">CURATED FOR YOU</div><h2>Places you could fall for</h2></div>
                <div class="section-link">Explore your shortlist ↓</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for rank, (_, row) in enumerate(recommendations.iterrows(), start=1):
            render_recommendation_card(row, rank, destinations, companion, budget)
        st.markdown(
            """
            <div class="concierge-card">
                <div class="concierge-title">Make it your own</div>
                <div class="concierge-copy">
                    Adjust your travel style, weather or budget in the planner to discover a different side of Europe.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with map_tab:
        st.header("Explore Destinations On The Map")
        st.markdown('<a id="map"></a>', unsafe_allow_html=True)
        render_map(recommendations, destinations)

    with data_tab:
        st.header("Destination Dataset")
        with st.expander("How your answers were translated"):
            st.json({"preferences": preferences, "weather_preference": effective_weather_preference})
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
