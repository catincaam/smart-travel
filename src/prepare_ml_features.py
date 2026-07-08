import pandas as pd


INPUT_PATH = "data/processed/destinations_feature_engineered.csv"
RAW_FEATURES_OUTPUT_PATH = "data/processed/ml_features_raw.csv"
SCALED_FEATURES_OUTPUT_PATH = "data/processed/ml_features_scaled.csv"
SCALING_SUMMARY_OUTPUT_PATH = "data/processed/ml_feature_scaling_summary.csv"

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

IDENTIFIER_COLUMNS = [
    "destination_name",
    "country",
]


def standard_scale(features):
    """
    StandardScaler logic:

        scaled_value = (value - column_mean) / column_standard_deviation

    We use population standard deviation (ddof=0), which matches the behavior
    of sklearn.preprocessing.StandardScaler.
    """
    means = features.mean()
    stds = features.std(ddof=0)

    scaled_features = (features - means) / stds

    scaling_summary = pd.DataFrame(
        {
            "feature": features.columns,
            "mean_before_scaling": means.values,
            "std_before_scaling": stds.values,
            "mean_after_scaling": scaled_features.mean().values,
            "std_after_scaling": scaled_features.std(ddof=0).values,
        }
    )

    return scaled_features, scaling_summary


def main():
    destinations = pd.read_csv(INPUT_PATH)

    raw_model_data = destinations[IDENTIFIER_COLUMNS + MODEL_FEATURES].copy()
    raw_model_data.to_csv(RAW_FEATURES_OUTPUT_PATH, index=False)

    scaled_features, scaling_summary = standard_scale(destinations[MODEL_FEATURES])

    scaled_model_data = pd.concat(
        [
            destinations[IDENTIFIER_COLUMNS].reset_index(drop=True),
            scaled_features.reset_index(drop=True),
        ],
        axis=1,
    )
    scaled_model_data.to_csv(SCALED_FEATURES_OUTPUT_PATH, index=False)
    scaling_summary.to_csv(SCALING_SUMMARY_OUTPUT_PATH, index=False)

    print("Done!")
    print("Selected model features:")
    print(MODEL_FEATURES)
    print("\nRaw feature preview:")
    print(raw_model_data.head())
    print("\nScaled feature summary:")
    print(scaling_summary)


if __name__ == "__main__":
    main()
