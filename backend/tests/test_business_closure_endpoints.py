from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_admin_dashboard_endpoint_has_business_kpis():
    response = client.get("/api/v1/admin/dashboard")
    assert response.status_code == 200
    item = response.json()["item"]
    assert "kpis" in item
    assert "work_order_metrics" in item
    assert "latest_anomalies" in item
    assert "next_actions" in item


def test_worker_dashboard_endpoint_filters_user_orders():
    response = client.get("/api/v1/admin/worker-dashboard/worker_ahu")
    assert response.status_code == 200
    item = response.json()["item"]
    assert "kpis" in item
    assert "items" in item


def test_anomaly_event_endpoint_aggregates_context():
    anomaly = client.get("/api/v1/analytics/anomalies").json()["items"][0]
    response = client.get(f"/api/v1/anomaly-events/{anomaly['record_id']}")
    assert response.status_code == 200
    item = response.json()["item"]
    assert item["record_id"] == anomaly["record_id"]
    assert "explanation" in item
    assert "linked_work_orders" in item
    assert "next_action" in item
