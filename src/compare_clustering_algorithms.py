import pandas as pd
from sklearn.cluster import AgglomerativeClustering, DBSCAN, KMeans
from sklearn.metrics import silhouette_score


INPUT_PATH = "data/processed/ml_features_scaled.csv"
OUTPUT_PATH = "data/processed/clustering_algorithm_comparison.csv"

MODEL_FEATURES = [
    "restaurant_count",
    "cafe_count",
    "bar_count",
    "museum_count",
    "park_count",
    "nearby_beach_count",
    "summer_avg_temp",
    "summer_avg_daily_rain",
]

RANDOM_STATE = 42


def safe_silhouette_score(features, labels):
    unique_labels = set(labels)
    non_noise_labels = {label for label in unique_labels if label != -1}

    if len(non_noise_labels) < 2:
        return None

    clustered_mask = labels != -1
    if clustered_mask.sum() < 3:
        return None

    return round(silhouette_score(features[clustered_mask], labels[clustered_mask]), 4)


def summarize_labels(labels):
    labels_series = pd.Series(labels)
    cluster_count = labels_series[labels_series != -1].nunique()
    noise_count = int((labels_series == -1).sum())
    largest_cluster_size = int(labels_series.value_counts().max())

    return cluster_count, noise_count, largest_cluster_size


def evaluate_model(features, model_name, labels, notes):
    cluster_count, noise_count, largest_cluster_size = summarize_labels(labels)

    return {
        "model": model_name,
        "cluster_count": cluster_count,
        "noise_count": noise_count,
        "largest_cluster_size": largest_cluster_size,
        "silhouette_score": safe_silhouette_score(features, labels),
        "notes": notes,
    }


def main():
    data = pd.read_csv(INPUT_PATH)
    features = data[MODEL_FEATURES].to_numpy(dtype=float)

    results = []

    for k in [2, 3, 4]:
        kmeans = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=20)
        labels = kmeans.fit_predict(features)
        results.append(
            evaluate_model(
                features,
                f"K-Means k={k}",
                labels,
                "Centroid-based clustering; works well with standardized numeric features.",
            )
        )

    for k in [2, 3, 4]:
        hierarchical = AgglomerativeClustering(n_clusters=k, linkage="ward")
        labels = hierarchical.fit_predict(features)
        results.append(
            evaluate_model(
                features,
                f"Hierarchical k={k}",
                labels,
                "Useful comparison model; creates nested distance-based groups.",
            )
        )

    for eps in [1.2, 1.5, 2.0]:
        dbscan = DBSCAN(eps=eps, min_samples=2)
        labels = dbscan.fit_predict(features)
        results.append(
            evaluate_model(
                features,
                f"DBSCAN eps={eps}",
                labels,
                "Density-based clustering; can mark outliers as noise but may struggle on small datasets.",
            )
        )

    results_df = pd.DataFrame(results)
    results_df.to_csv(OUTPUT_PATH, index=False)

    print(results_df.to_string(index=False))
    print(f"\nSaved comparison to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
