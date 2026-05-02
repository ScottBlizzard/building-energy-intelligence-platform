from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_time_summary_endpoint():
    response = client.get("/api/v1/analytics/time-summary")
    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)


def test_time_summary_with_freq_parameter():
    for freq in ["H", "D", "W", "M"]:
        response = client.get("/api/v1/analytics/time-summary", params={"freq": freq})
        assert response.status_code == 200


def test_building_comparison_endpoint():
    response = client.get("/api/v1/analytics/building-comparison")
    assert response.status_code == 200
    items = response.json()["items"]
    assert isinstance(items, list)
    assert len(items) >= 1


def test_building_comparison_has_required_fields():
    response = client.get("/api/v1/analytics/building-comparison")
    item = response.json()["items"][0]
    assert "building_id" in item
    assert "building_name" in item
    assert "electricity_kwh" in item
    assert "average_cop" in item


def test_cop_ranking_endpoint():
    response = client.get("/api/v1/analytics/cop-ranking")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) >= 1
    assert "average_cop" in items[0]


def test_cop_ranking_is_sorted():
    response = client.get("/api/v1/analytics/cop-ranking")
    items = response.json()["items"]
    cops = [item["average_cop"] for item in items]
    assert cops == sorted(cops, reverse=True)


def test_anomalies_endpoint():
    response = client.get("/api/v1/analytics/anomalies")
    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)


def test_anomalies_with_building_filter():
    buildings = client.get("/api/v1/buildings").json()["items"]
    building_id = buildings[0]["building_id"]
    response = client.get(
        "/api/v1/analytics/anomalies", params={"building_id": building_id}
    )
    assert response.status_code == 200


def test_anomaly_reason_endpoint():
    response = client.get("/api/v1/analytics/anomaly-reasons")
    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)

