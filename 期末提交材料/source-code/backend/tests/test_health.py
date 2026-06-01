from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint_returns_ok():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_endpoint_returns_expected_fields():
    response = client.get("/api/v1/health")
    payload = response.json()
    assert "environment" in payload
    assert "data_file" in payload
    assert "knowledge_base_dir" in payload

