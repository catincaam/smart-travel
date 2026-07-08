from pathlib import Path

import folium
import pandas as pd


INPUT_PATH = Path("data/processed/destinations_clustered.csv")
OUTPUT_DIR = Path("maps")
OUTPUT_PATH = OUTPUT_DIR / "smart_travel_map.html"


def clamp(value, minimum=0, maximum=100):
    return max(minimum, min(maximum, value))


def star_rating(score):
    filled_stars = round(score / 20)
    empty_stars = 5 - filled_stars
    return ("*" * filled_stars) + ("." * empty_stars)


def weather_score(row):
    ideal_temp = 27
    temp_tolerance = 12
    temp_score = clamp(100 - (abs(row["summer_avg_temp"] - ideal_temp) / temp_tolerance * 100))
    rain_score = clamp(100 - (row["summer_avg_daily_rain"] * 20))
    return round((0.7 * temp_score) + (0.3 * rain_score), 2)


def color_for_score(score, mode):
    if score >= 80:
        return {
            "weather": "green",
            "beach": "blue",
            "culture": "purple",
        }[mode]

    if score >= 50:
        return "orange"

    return "red"


def marker_radius(score):
    return 6 + (score / 100 * 9)


def popup_html(row, active_score_name, active_score):
    return f"""
    <div style="font-family: Arial, sans-serif; min-width: 230px;">
        <h3 style="margin: 0 0 6px 0;">{row["destination_name"]}</h3>
        <p style="margin: 0 0 8px 0;"><strong>{row["country"]}</strong></p>
        <p style="margin: 0;"><strong>Cluster:</strong> {row["cluster_profile"]}</p>
        <p style="margin: 0;"><strong>Travel style:</strong> {row["dominant_travel_style"]}</p>
        <hr>
        <p style="margin: 0;"><strong>{active_score_name}:</strong> {active_score:.1f} / 100</p>
        <p style="margin: 0;"><strong>Weather:</strong> {row["summer_weather_score"]:.1f} / 100 {star_rating(row["summer_weather_score"])}</p>
        <p style="margin: 0;"><strong>Food:</strong> {row["food_score"]:.1f} / 100 {star_rating(row["food_score"])}</p>
        <p style="margin: 0;"><strong>Beach:</strong> {row["beach_score"]:.1f} / 100 {star_rating(row["beach_score"])}</p>
        <p style="margin: 0;"><strong>Culture:</strong> {row["culture_score"]:.1f} / 100 {star_rating(row["culture_score"])}</p>
        <p style="margin: 0;"><strong>Nature:</strong> {row["nature_score"]:.1f} / 100 {star_rating(row["nature_score"])}</p>
        <hr>
        <p style="margin: 0;"><strong>Summer temp:</strong> {row["summer_avg_temp"]:.1f} C</p>
        <p style="margin: 0;"><strong>Summer rain:</strong> {row["summer_avg_daily_rain"]:.1f} mm/day</p>
    </div>
    """


def add_score_layer(map_object, df, layer_name, score_column, mode):
    layer = folium.FeatureGroup(name=layer_name, show=(mode == "weather"))

    for _, row in df.iterrows():
        score = row[score_column]
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=marker_radius(score),
            color=color_for_score(score, mode),
            fill=True,
            fill_color=color_for_score(score, mode),
            fill_opacity=0.72,
            weight=2,
            popup=folium.Popup(
                popup_html(row, layer_name, score),
                max_width=320,
            ),
            tooltip=f"{row['destination_name']} - {score:.1f}/100",
        ).add_to(layer)

    layer.add_to(map_object)


def build_map(df):
    destination_map = folium.Map(
        location=[47.0, 12.0],
        zoom_start=4,
        tiles="CartoDB positron",
    )

    add_score_layer(
        destination_map,
        df,
        "Summer Weather Score",
        "summer_weather_score",
        "weather",
    )
    add_score_layer(destination_map, df, "Beach Score", "beach_score", "beach")
    add_score_layer(destination_map, df, "Culture Score", "culture_score", "culture")

    folium.LayerControl(collapsed=False).add_to(destination_map)

    legend = """
    <div style="
        position: fixed;
        bottom: 35px;
        left: 35px;
        z-index: 9999;
        background: white;
        padding: 12px 14px;
        border: 1px solid #999;
        border-radius: 6px;
        font-family: Arial, sans-serif;
        font-size: 13px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    ">
        <strong>Smart Travel Map</strong><br>
        Green / Blue / Purple: 80+<br>
        Orange: 50-79<br>
        Red: below 50<br>
        Marker size increases with score.
    </div>
    """
    destination_map.get_root().html.add_child(folium.Element(legend))

    return destination_map


def main():
    df = pd.read_csv(INPUT_PATH)
    df["summer_weather_score"] = df.apply(weather_score, axis=1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    smart_travel_map = build_map(df)
    smart_travel_map.save(OUTPUT_PATH)

    print(f"Created interactive map: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
