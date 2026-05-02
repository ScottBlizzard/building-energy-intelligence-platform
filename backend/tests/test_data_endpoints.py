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


def test_dataset_meta_has_time_range():
    response = client.get("/api/v1/dataset-meta")
    payload = response.json()
    assert "time_range" in payload
    assert "start" in payload["time_range"]
    assert "end" in payload["time_range"]


def test_buildings_endpoint():
    response = client.get("/api/v1/buildings")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) >= 1
    assert "building_id" in payload["items"][0]


def test_buildings_have_required_fields():
    response = client.get("/api/v1/buildings")
    item = response.json()["items"][0]
    assert "building_id" in item
    assert "building_name" in item
    assert "building_type" in item


def test_overview_endpoint():
    response = client.get("/api/v1/overview")
    assert response.status_code == 200
    payload = response.json()
    assert "total_records" in payload
    assert "building_count" in payload
    assert "average_cop" in payload
    assert "abnormal_record_count" in payload
    assert "time_range" in payload
    assert "totals" in payload


def test_records_filter_by_building():
    buildings = client.get("/api/v1/buildings").json()["items"]
    building_id = buildings[0]["building_id"]
    response = client.get("/api/v1/records", params={"building_id": building_id, "limit": 5})
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] <= 5
    assert all(item["building_id"] == building_id for item in payload["items"])


def test_records_respects_limit():
    response = client.get("/api/v1/records", params={"limit": 3})
    assert response.status_code == 200
    assert response.json()["count"] <= 3


def test_records_default_limit():
    response = client.get("/api/v1/records")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] <= 100
    assert "total_filtered_count" in payload
    assert "items" in payload

