"""Tests for the building-detail analytics endpoint."""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_building_detail_requires_building_id():
    response = client.get("/api/v1/analytics/building-detail")
    assert response.status_code == 422  # missing required param


def test_building_detail_with_valid_building_id():
    buildings = client.get("/api/v1/buildings").json()["items"]
    building_id = buildings[0]["building_id"]
    response = client.get(
        "/api/v1/analytics/building-detail",
        params={"building_id": building_id},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["building_id"] == building_id
    assert payload["building_name"] is not None
    assert payload["building_type"] is not None
    assert "record_count" in payload
    assert "totals" in payload
    assert "average_cop" in payload
    assert "anomaly_count" in payload
    assert "top_anomaly_reasons" in payload
    assert "recent_records" in payload
    assert "time_range" in payload


def test_building_detail_totals_have_required_fields():
    buildings = client.get("/api/v1/buildings").json()["items"]
    building_id = buildings[0]["building_id"]
    response = client.get(
        "/api/v1/analytics/building-detail",
        params={"building_id": building_id},
    )
    totals = response.json()["totals"]
    assert "electricity_kwh" in totals
    assert "water_m3" in totals
    assert "hvac_kwh" in totals
    assert "cooling_load_kwh" in totals


def test_building_detail_invalid_building_id():
    response = client.get(
        "/api/v1/analytics/building-detail",
        params={"building_id": "NONEXISTENT"},
    )
    assert response.status_code == 404


def test_building_detail_with_time_filter():
    buildings = client.get("/api/v1/buildings").json()["items"]
    building_id = buildings[0]["building_id"]
    response = client.get(
        "/api/v1/analytics/building-detail",
        params={
            "building_id": building_id,
            "start_time": "2026-03-01T00:00:00",
            "end_time": "2026-03-02T00:00:00",
        },
    )
    assert response.status_code == 200
    assert response.json()["record_count"] >= 0


def test_building_detail_all_buildings():
    """Verify building-detail works for every known building."""
    buildings = client.get("/api/v1/buildings").json()["items"]
    for b in buildings:
        response = client.get(
            "/api/v1/analytics/building-detail",
            params={"building_id": b["building_id"]},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["building_name"] == b["building_name"]
