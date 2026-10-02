from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

from src.api import app
from src import recommend

ROOT = Path(__file__).resolve().parents[1]
PREFERENCES = dict(food=6, beach=8, culture=5, nature=4, nightlife=2)


@pytest.mark.parametrize('month,season', [('January', 'winter'), ('April', 'spring'), ('August', 'summer'), ('October', 'autumn')])
def test_weather_facts_match_selected_season(month, season):
    results = recommend.recommend_destinations(PREFERENCES, travel_month=month)
    source = pd.read_csv(recommend.INPUT_PATH).set_index('destination_name')
    assert set(results.travel_season) == {season}
    for _, row in results.iterrows():
        assert row.season_avg_temp == source.loc[row.destination_name, f'{season}_avg_temp']
        assert row.season_avg_daily_rain == source.loc[row.destination_name, f'{season}_avg_daily_rain']


def test_recommendations_work_outside_repository(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert len(recommend.recommend_destinations(PREFERENCES, top_n=2)) == 2


@pytest.mark.parametrize('field,value', [('budget','cheap'), ('companion','Nobody'), ('weather_preference','sunny'), ('top_n',0), ('food',11)])
def test_api_rejects_invalid_preferences(field, value):
    payload = {**PREFERENCES, 'month': 'August', field: value}
    response = TestClient(app).post('/recommend', json=payload)
    assert response.status_code == 422


def test_api_serializes_recommendations_and_rejects_invalid_month():
    client = TestClient(app)
    response = client.post('/recommend', json={**PREFERENCES, 'month': 'January', 'top_n': 2})
    assert response.status_code == 200
    body = response.json()
    assert len(body['recommendations']) == 2
    assert body['recommendations'][0]['travel_season'] == 'winter'
    assert client.post('/recommend', json={**PREFERENCES, 'month': 'invalid'}).status_code == 400


def test_dashboard_month_change_updates_visible_weather():
    dashboard = AppTest.from_file(str(ROOT / 'dashboard/streamlit_app.py')).run(timeout=30)
    assert not dashboard.exception
    assert dashboard.text_area[0].value == ''
    dashboard.selectbox[0].select('January').run(timeout=30)
    assert not dashboard.exception
    cards = [item.value for item in dashboard.markdown if 'class="destination-card"' in item.value]
    assert len(cards) == 5
    assert all('Winter weather' in card and 'Summer weather' not in card for card in cards)
