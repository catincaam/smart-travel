# Data quality checks

Run `python -m src.data_quality --output /tmp/data-quality.json` from the repository
root. `--input PATH` checks another final destination CSV. Exit status is 1 for
blocking issues and 0 otherwise; unusual counts are warnings. Files are never
rewritten, imputed, deduplicated or deleted by this validator.

The recommendation loader applies the same checks to its final enriched dataset
before computing scores. Invalid data stops recommendations; the API returns 503
and the dashboard shows a review message. The dashboard's Dataset tab displays
source notes, per-destination availability, issues and a downloadable JSON report.

Rules:
- Required names, country, profile, cost category and numeric features must exist.
- Name + country must be unique after trimming and case-folding. No fuzzy merging.
- Leading/trailing whitespace in labels is flagged for review, not silently changed.
- Coordinates: latitude [-90, 90], longitude [-180, 180]. This does not establish
  that coordinates belong to the intended destination.
- All numeric features must be finite; counts must be nonnegative integers;
  search radius must be positive; cost index must be nonnegative.
- Seasonal mean temperature: [-60, 60] °C; mean daily rain: [0, 100] mm/day.
  These are broad sanity bounds, not precise local climatological checks.
- Cost categories and destination profiles must use the supported labels.
- Counts above Q3 + 3×IQR are review flags when at least four valid observations
  and a nonzero IQR exist. They remain in the dataset and recommendations.

Missing observations are errors, not zero counts. Recorded zero counts are valid,
but may reflect source coverage rather than absence of places in reality.
Availability means present and within these rules, not verified factual truth.
The report timestamp is the check time. The current dataset does not contain
collection timestamps, so freshness cannot be certified. Costs remain proxies.
