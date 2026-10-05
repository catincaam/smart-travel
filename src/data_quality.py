"""Read-only checks for the final destination dataset, before scoring.

Rules establish completeness and plausibility, not factual correctness.
Run: python -m src.data_quality --output /tmp/data-quality.json
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / 'data/processed/destinations_clustered.csv'
COUNTS = ('restaurant_count', 'cafe_count', 'bar_count', 'museum_count', 'park_count', 'nearby_beach_count')
WEATHER = tuple(f'{season}_{measure}' for season in ('winter', 'spring', 'summer', 'autumn') for measure in ('avg_temp', 'avg_daily_rain'))
TEXT = ('destination_name', 'country', 'cluster_profile', 'dominant_travel_style', 'climate_category', 'cost_level')
GROUPS = {
    'Location': ('latitude', 'longitude'),
    'Seasonal weather': WEATHER,
    'Nearby places': COUNTS + ('search_radius_m',),
    'Cost proxy': ('cost_of_living_index', 'cost_level'),
}
NUMERIC = ('latitude', 'longitude', 'cost_of_living_index', 'search_radius_m') + COUNTS + WEATHER
REQUIRED = TEXT + NUMERIC


class DataQualityError(ValueError):
    """Invalid source data must not silently become a recommendation."""


def inspect_destinations(df):
    issues = []
    validity = {}

    def issue(severity, code, column, position, message):
        name = None if position is None or 'destination_name' not in df else str(df.iloc[position]['destination_name'])
        issues.append(dict(severity=severity, code=code, column=column,
                           row=None if position is None else position + 2,
                           destination=name, message=message))

    if df.empty:
        issue('error', 'empty_dataset', None, None, 'No destinations are available.')
    for column in REQUIRED:
        if column not in df:
            issue('error', 'missing_column', column, None, 'Required column is missing.')
            validity[column] = [False] * len(df)
            continue
        validity[column] = []
        for position, value in enumerate(df[column]):
            valid = True
            if pd.isna(value) or (isinstance(value, str) and not value.strip()):
                issue('error', 'missing_value', column, position, 'Unknown value; do not replace with zero.')
                valid = False
            elif column in TEXT:
                if not isinstance(value, str):
                    issue('error', 'invalid_type', column, position, 'Expected a text label.')
                    valid = False
                elif value != value.strip():
                    issue('error', 'noncanonical_label', column, position, 'Leading or trailing whitespace must be reviewed before joining.')
                    valid = False
                elif column == 'cost_level' and value not in ('Budget', 'Mid-range', 'Luxury'):
                    issue('error', 'invalid_category', column, position, 'Expected Budget, Mid-range or Luxury.')
                    valid = False
                elif column == 'cluster_profile' and value not in ('Warm Coastal & Beach', 'Urban Culture & Food', 'Cool Balanced & Nature'):
                    issue('error', 'invalid_category', column, position, 'Unknown destination profile; check cluster enrichment.')
                    valid = False
            else:
                # Numeric strings are not silently converted in the runtime dataframe.
                if isinstance(value, (str, bool)) or not isinstance(value, (int, float)):
                    issue('error', 'invalid_type', column, position, 'Expected a numeric value.')
                    valid = False
                else:
                    lower, upper = 0, float('inf')
                    if column == 'latitude':
                        lower, upper = -90, 90
                    elif column == 'longitude':
                        lower, upper = -180, 180
                    elif column.endswith('_avg_temp'):
                        lower, upper = -60, 60
                    elif column.endswith('_avg_daily_rain'):
                        upper = 100
                    valid = lower <= value <= upper and abs(value) != float('inf')
                    if column == 'search_radius_m':
                        valid = valid and value > 0
                    if column in COUNTS:
                        valid = valid and value == int(value) if valid else False
                    if not valid:
                        issue('error', 'invalid_range', column, position, 'Value violates the documented range or count rule.')
            validity[column].append(valid)

    if {'destination_name', 'country'}.issubset(df.columns):
        keys = df[['destination_name', 'country']].astype('string').apply(lambda col: col.str.strip().str.casefold())
        for position, duplicate in enumerate(keys.duplicated(keep=False)):
            if duplicate:
                issue('error', 'duplicate_destination', 'destination_name,country', position, 'Duplicate normalized name + country; no rows removed automatically.')

    for column in COUNTS:
        if column not in df:
            continue
        values = pd.to_numeric(df[column], errors='coerce')
        valid_values = values[pd.Series(validity[column], index=df.index)]
        if len(valid_values) < 4:
            continue
        q1, q3 = valid_values.quantile([0.25, 0.75])
        if q3 <= q1:
            continue
        threshold = q3 + 3 * (q3 - q1)
        for position, value in enumerate(values):
            if validity[column][position] and value > threshold:
                issue('warning', 'unusual_count', column, position, 'Above Q3 + 3×IQR. May be genuine; investigate rather than delete.')

    coverage = []
    for position in range(len(df)):
        entry = {'destination': str(df.iloc[position].get('destination_name', 'Unknown')),
                 'country': str(df.iloc[position].get('country', 'Unknown'))}
        for group, columns in GROUPS.items():
            entry[group] = 'Available' if all(validity[c][position] for c in columns) else 'Missing / invalid'
        coverage.append(entry)
    errors = sum(i['severity'] == 'error' for i in issues)
    warnings = sum(i['severity'] == 'warning' for i in issues)
    return {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'rows': len(df),
            'status': 'blocked' if errors else ('review' if warnings else 'passed'),
            'errors': errors, 'warnings': warnings, 'issues': issues, 'coverage': coverage,
            'note': 'Availability and rule checks do not certify accuracy or freshness. Check time is not data collection time.'}


def require_valid_destinations(df):
    report = inspect_destinations(df)
    if report['errors']:
        raise DataQualityError(f"Destination data failed {report['errors']} quality checks. Run python -m src.data_quality for details.")
    return df


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=DEFAULT_INPUT)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = inspect_destinations(pd.read_csv(args.input))
    content = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(content + '\n', encoding='utf-8')
    print(content)
    return 1 if report['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
