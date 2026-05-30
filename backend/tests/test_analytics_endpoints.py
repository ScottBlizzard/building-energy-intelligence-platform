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


def test_anomalies_with_floor_filter():
    first = client.get("/api/v1/records", params={"limit": 1}).json()["items"][0]
    response = client.get(
        "/api/v1/analytics/anomalies",
        params={
            "building_id": first["building_id"],
            "floor_label": first["floor_label"],
        },
    )
    assert response.status_code == 200
    assert all(item["floor_label"] == first["floor_label"] for item in response.json()["items"])
    assert isinstance(response.json()["items"], list)


def test_floor_summary_endpoint():
    response = client.get("/api/v1/analytics/floor-summary")
    assert response.status_code == 200
    items = response.json()["items"]
    assert isinstance(items, list)
    assert len(items) > 4
    assert "floor_label" in items[0]
    assert "zone_name" in items[0]
    assert "anomaly_count" in items[0]


def test_floor_filter_anomaly_count_matches_floor_summary():
    building_id = "BLD-A"
    summary = client.get(
        "/api/v1/analytics/floor-summary", params={"building_id": building_id}
    ).json()["items"]
    counts_by_floor = {}
    for item in summary:
        counts_by_floor[item["floor_label"]] = counts_by_floor.get(item["floor_label"], 0) + item[
            "anomaly_count"
        ]

    assert counts_by_floor
    for floor_label, expected_count in counts_by_floor.items():
        response = client.get(
            "/api/v1/analytics/anomalies",
            params={"building_id": building_id, "floor_label": floor_label},
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) == expected_count


def test_equipment_summary_endpoint():
    response = client.get("/api/v1/analytics/equipment-summary")
    assert response.status_code == 200
    items = response.json()["items"]
    assert isinstance(items, list)
    assert len(items) > 4
    assert "equipment_type" in items[0]
    assert "priority" in items[0]
    assert "maintenance_hint" in items[0]


def test_work_orders_endpoint():
    response = client.get("/api/v1/analytics/work-orders")
    assert response.status_code == 200
    items = response.json()["items"]
    assert isinstance(items, list)
    if items:
        assert "work_order_id" in items[0]
        assert "recommended_action" in items[0]


def test_work_orders_with_floor_filter():
    first = client.get("/api/v1/records", params={"limit": 1}).json()["items"][0]
    response = client.get(
        "/api/v1/analytics/work-orders",
        params={
            "building_id": first["building_id"],
            "floor_label": first["floor_label"],
        },
    )
    assert response.status_code == 200
    assert all(item["floor_label"] == first["floor_label"] for item in response.json()["items"])


def test_optimization_recommendations_endpoint():
    response = client.get("/api/v1/analytics/optimization-recommendations")
    assert response.status_code == 200
    items = response.json()["items"]
    assert isinstance(items, list)
    assert "recommendation_id" in items[0]
    assert "expected_impact" in items[0]


def test_anomaly_explanation_endpoint():
    anomaly = client.get("/api/v1/analytics/anomalies").json()["items"][0]
    response = client.get(f"/api/v1/analytics/anomaly-explanations/{anomaly['record_id']}")
    assert response.status_code == 200
    item = response.json()["item"]
    assert item["record_id"] == anomaly["record_id"]
    assert "triggered_rules" in item
    assert "recommended_action" in item


def test_floor_registry_endpoint():
    response = client.get("/api/v1/analytics/floor-registry", params={"building_id": "BLD-A"})
    assert response.status_code == 200
    items = response.json()["items"]
    assert isinstance(items, list)
    assert items
    assert "risk_level" in items[0]
    assert "owner" in items[0]


def test_operation_report_endpoint():
    response = client.get("/api/v1/analytics/operation-report")
    assert response.status_code == 200
    item = response.json()["item"]
    assert "overview" in item
    assert "action_items" in item

