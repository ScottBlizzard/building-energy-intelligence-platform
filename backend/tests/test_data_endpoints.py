from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_dataset_meta_endpoint():
    response = client.get("/api/v1/dataset-meta")
    assert response.status_code == 200
    payload = response.json()
    assert "fields" in payload
    assert "building_options" in payload
    assert payload["record_count"] >= 1


def test_buildings_endpoint():
    response = client.get("/api/v1/buildings")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) >= 1
    assert "building_id" in payload["items"][0]


def test_records_filter_by_building():
    buildings = client.get("/api/v1/buildings").json()["items"]
    building_id = buildings[0]["building_id"]
    response = client.get("/api/v1/records", params={"building_id": building_id, "limit": 5})
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] <= 5
    assert all(item["building_id"] == building_id for item in payload["items"])

