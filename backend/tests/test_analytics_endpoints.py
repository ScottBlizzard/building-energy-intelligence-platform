from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_time_summary_endpoint():
    response = client.get("/api/v1/analytics/time-summary")
    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)


def test_cop_ranking_endpoint():
    response = client.get("/api/v1/analytics/cop-ranking")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) >= 1
    assert "average_cop" in items[0]


def test_anomaly_reason_endpoint():
    response = client.get("/api/v1/analytics/anomaly-reasons")
    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)

