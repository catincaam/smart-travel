import numpy as np
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
from evaluate_kmeans_clusters import MODEL_FEATURES, fit_kmeans


DESTINATIONS_PATH = "data/processed/destinations_feature_engineered.csv"
SCALED_FEATURES_PATH = "data/processed/ml_features_scaled.csv"

ASSIGNMENTS_OUTPUT_TEMPLATE = "data/processed/kmeans_k{k}_assignments.csv"
PROFILES_OUTPUT_TEMPLATE = "data/processed/kmeans_k{k}_profiles.csv"

K_VALUES = [2, 3]
RANDOM_STATE = 42


def main():
    destinations = pd.read_csv(DESTINATIONS_PATH)
    scaled_features = pd.read_csv(SCALED_FEATURES_PATH)
    x = scaled_features[MODEL_FEATURES].to_numpy(dtype=float)
    rng = np.random.default_rng(RANDOM_STATE)

    for k in K_VALUES:
        labels, _, _ = fit_kmeans(x, k, rng)

        clustered = destinations.copy()
        clustered["cluster"] = labels

        assignments = clustered[
            [
                "destination_name",
                "country",
                "cluster",
                "dominant_travel_style",
                "climate_category",
                "overall_score",
                *MODEL_FEATURES,
            ]
        ].sort_values(["cluster", "destination_name"])

        profiles = (
            clustered.groupby("cluster")[
                [
                    *MODEL_FEATURES,
                    "food_score",
                    "nightlife_score",
                    "culture_score",
                    "nature_score",
                    "beach_score",
                    "overall_score",
                ]
            ]
            .mean()
            .round(2)
        )
        profiles["destination_count"] = clustered.groupby("cluster").size()
        profiles = profiles.reset_index()

        assignments_path = ASSIGNMENTS_OUTPUT_TEMPLATE.format(k=k)
        profiles_path = PROFILES_OUTPUT_TEMPLATE.format(k=k)

        assignments.to_csv(assignments_path, index=False)
        profiles.to_csv(profiles_path, index=False)

        print(f"\nK={k} assignments")
        print(assignments[["destination_name", "country", "cluster"]].to_string(index=False))
        print(f"\nK={k} profiles")
        print(profiles.to_string(index=False))


if __name__ == "__main__":
    main()
