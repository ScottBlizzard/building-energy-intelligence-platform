from app.mcp_server import (
    get_admin_business_dashboard,
    get_anomaly_event_context,
    get_worker_business_dashboard,
    list_persistent_work_orders,
)


def test_mcp_admin_dashboard_tool_returns_business_queues():
    payload = get_admin_business_dashboard()

    assert "kpis" in payload
    assert "work_order_metrics" in payload
    assert "next_actions" in payload


def test_mcp_work_order_tool_returns_metrics():
    payload = list_persistent_work_orders(limit=5)

    assert "metrics" in payload
    assert "items" in payload
    assert isinstance(payload["items"], list)


def test_mcp_worker_dashboard_tool_scopes_to_worker():
    payload = get_worker_business_dashboard("worker_ahu")

    assert "kpis" in payload
    assert "items" in payload
    assert all(item.get("assignee_id") == "worker_ahu" for item in payload["items"])


def test_mcp_anomaly_event_context_tool_handles_existing_record():
    orders = list_persistent_work_orders(limit=1)["items"]
    record_id = orders[0].get("source_record_id") if orders else "REC-20260301-0001"

    payload = get_anomaly_event_context(record_id)

    assert "item" in payload
