import numpy as np
import pandas as pd


INPUT_PATH = "data/processed/ml_features_scaled.csv"
OUTPUT_PATH = "data/processed/kmeans_cluster_metrics.csv"

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

K_VALUES = range(2, 7)
RANDOM_STATE = 42
N_INIT = 20
MAX_ITER = 300


def assign_clusters(x, centroids):
    distances = np.linalg.norm(x[:, np.newaxis, :] - centroids[np.newaxis, :, :], axis=2)
    return distances.argmin(axis=1)


def fit_kmeans(x, n_clusters, rng):
    best_labels = None
    best_centroids = None
    best_inertia = np.inf

    for _ in range(N_INIT):
        initial_indices = rng.choice(len(x), size=n_clusters, replace=False)
        centroids = x[initial_indices].copy()

        for _ in range(MAX_ITER):
            labels = assign_clusters(x, centroids)
            new_centroids = centroids.copy()

            for cluster_id in range(n_clusters):
                cluster_points = x[labels == cluster_id]
                if len(cluster_points) > 0:
                    new_centroids[cluster_id] = cluster_points.mean(axis=0)

            if np.allclose(centroids, new_centroids):
                break

            centroids = new_centroids

        labels = assign_clusters(x, centroids)
        inertia = sum(
            np.sum((x[labels == cluster_id] - centroids[cluster_id]) ** 2)
            for cluster_id in range(n_clusters)
        )

        if inertia < best_inertia:
            best_labels = labels
            best_centroids = centroids
            best_inertia = inertia

    return best_labels, best_centroids, best_inertia


def silhouette_score_manual(x, labels):
    scores = []
    unique_labels = np.unique(labels)

    for index, point in enumerate(x):
        own_cluster = labels[index]
        same_cluster_points = x[labels == own_cluster]

        if len(same_cluster_points) <= 1:
            scores.append(0)
            continue

        same_distances = np.linalg.norm(same_cluster_points - point, axis=1)
        a = same_distances[same_distances > 0].mean()

        other_cluster_distances = []
        for other_cluster in unique_labels:
            if other_cluster == own_cluster:
                continue

            other_points = x[labels == other_cluster]
            other_distances = np.linalg.norm(other_points - point, axis=1)
            other_cluster_distances.append(other_distances.mean())

        b = min(other_cluster_distances)
        scores.append((b - a) / max(a, b))

    return float(np.mean(scores))


def main():
    data = pd.read_csv(INPUT_PATH)
    x = data[MODEL_FEATURES].to_numpy(dtype=float)
    rng = np.random.default_rng(RANDOM_STATE)

    metrics = []
    for k in K_VALUES:
        labels, _, inertia = fit_kmeans(x, k, rng)
        silhouette = silhouette_score_manual(x, labels)
        metrics.append(
            {
                "k": k,
                "inertia": round(inertia, 4),
                "silhouette_score": round(silhouette, 4),
            }
        )

    metrics_df = pd.DataFrame(metrics)
    metrics_df.to_csv(OUTPUT_PATH, index=False)

    print(metrics_df.to_string(index=False))


if __name__ == "__main__":
    main()
