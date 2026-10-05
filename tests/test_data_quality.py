import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

from src import recommend
from src.api import app
from src.data_quality import DEFAULT_INPUT, DataQualityError, inspect_destinations, require_valid_destinations


@pytest.fixture
def data():
    return pd.read_csv(DEFAULT_INPUT)


def test_current_dataset_and_inspection_are_read_only(data):
    before = data.copy(deep=True)
    report = inspect_destinations(data)
    assert report['errors'] == 0
    assert len(report['coverage']) == len(data)
    pd.testing.assert_frame_equal(data, before)
    json.dumps(report, allow_nan=False)


@pytest.mark.parametrize('column,value,code', [
    ('latitude', 91, 'invalid_range'), ('longitude', -181, 'invalid_range'),
    ('restaurant_count', -1, 'invalid_range'), ('museum_count', 1.5, 'invalid_range'),
    ('winter_avg_temp', float('inf'), 'invalid_range'),
    ('summer_avg_daily_rain', -0.1, 'invalid_range'),
    ('search_radius_m', 0, 'invalid_range'), ('cost_of_living_index', -3, 'invalid_range'),
    ('cost_level', 'Unknown', 'invalid_category'),
    ('cluster_profile', '', 'missing_value'), ('country', ' Italy ', 'noncanonical_label'),
    ('latitude', 'north', 'invalid_type'),
])
def test_invalid_values_block_scoring(data, column, value, code):
    data[column] = data[column].astype(object)
    data.loc[0, column] = value
    report = inspect_destinations(data)
    assert any(i['column'] == column and i['code'] == code for i in report['issues'])
    with pytest.raises(DataQualityError):
        require_valid_destinations(data)


def test_missing_and_zero_are_distinct(data):
    data.loc[0, 'nearby_beach_count'] = 0
    assert inspect_destinations(data)['coverage'][0]['Nearby places'] == 'Available'
    data.loc[0, 'nearby_beach_count'] = float('nan')
    report = inspect_destinations(data)
    assert report['coverage'][0]['Nearby places'] == 'Missing / invalid'
    assert report['errors'] == 1


def test_missing_column_and_empty_data(data):
    assert inspect_destinations(data.drop(columns=['latitude']))['errors'] > 0
    assert inspect_destinations(data.iloc[:0])['status'] == 'blocked'


def test_duplicate_normalized_name_and_country(data):
    duplicate = data.iloc[[0]].copy()
    duplicate['destination_name'] = duplicate.destination_name.str.upper()
    both = pd.concat([data, duplicate], ignore_index=True)
    assert any(i['code'] == 'duplicate_destination' for i in inspect_destinations(both)['issues'])
    both.loc[len(both)-1, 'country'] = 'Another country'
    assert not any(i['code'] == 'duplicate_destination' for i in inspect_destinations(both)['issues'])


def test_outlier_is_flagged_but_preserved(data):
    data.loc[0, 'restaurant_count'] = 10000000
    report = inspect_destinations(data)
    assert report['errors'] == 0
    assert any(i['code'] == 'unusual_count' for i in report['issues'])
    assert require_valid_destinations(data).loc[0, 'restaurant_count'] == 10000000


def test_loader_rejects_invalid_enriched_data(data, tmp_path, monkeypatch):
    # Both complete and narrow clustering files must validate the final merged data.
    data.loc[0, 'cost_level'] = 'Unknown'
    enriched = tmp_path / 'enriched.csv'
    data.to_csv(enriched, index=False)
    monkeypatch.setattr(recommend, 'FEATURE_ENGINEERED_PATH', enriched)
    clusters = tmp_path / 'clusters.csv'
    data[['destination_name', 'country', 'cluster', 'cluster_profile']].to_csv(clusters, index=False)
    monkeypatch.setattr(recommend, 'INPUT_PATH', clusters)
    with pytest.raises(DataQualityError):
        recommend.load_destinations()


def test_api_returns_service_error_for_bad_source_data(monkeypatch):
    def invalid():
        raise DataQualityError('bad source data')
    monkeypatch.setattr(recommend, 'load_destinations', invalid)
    response = TestClient(app).post('/recommend', json=dict(food=5, beach=5, culture=5, nature=5, nightlife=5, month='August'))
    assert response.status_code == 503


def test_cli_reports_failure_without_changing_input(data, tmp_path):
    data.loc[0, 'latitude'] = 999
    source, output = tmp_path / 'input.csv', tmp_path / 'report.json'
    data.to_csv(source, index=False)
    before = source.read_bytes()
    result = subprocess.run([sys.executable, '-m', 'src.data_quality', '--input', str(source), '--output', str(output)], capture_output=True)
    assert result.returncode == 1
    assert json.loads(output.read_text())['status'] == 'blocked'
    assert source.read_bytes() == before


def test_dashboard_shows_report():
    dashboard = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'dashboard/streamlit_app.py')).run(timeout=30)
    assert not dashboard.exception
    assert any(item.value == 'Data quality & sources' for item in dashboard.subheader)
    assert any(item.label == 'Blocking issues' and item.value == '0' for item in dashboard.metric)
