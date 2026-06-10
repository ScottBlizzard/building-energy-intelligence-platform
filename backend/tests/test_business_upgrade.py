"""Tests for the latest business-closure upgrade:

- auto-confirm-queue batch draft creation and idempotency
- before/after estimate capture, rounding and estimate flag
- before_kwh/before_cop flowing through the normal create path (schema)
- corrected default status for unassigned work orders
- closed cases surfaced in the operation report with estimate wording
"""
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

client = TestClient(app)


def _base_payload(**overrides):
    payload = {
        "source_record_id": "R-UP-1",
        "priority": "高",
        "building_id": "BLD-C",
        "building_name": "图书信息楼C",
        "floor_label": "4F",
        "zone_name": "阅读区",
        "equipment_id": "AHU-C-4F-06",
        "equipment_type": "空气处理机组",
        "timestamp": "2026-06-01 21:00:00",
        "anomaly_reason": "设备状态异常",
        "possible_cause": "设备告警",
        "recommended_action": "检查 AHU 运行状态",
        "owner_role": "空调系统运维员",
        "assignee_id": "worker_ahu",
        "before_kwh": 137.0,
        "before_cop": 2.0,
    }
    payload.update(overrides)
    return payload


def _isolate(tmp_path, monkeypatch):
    monkeypatch.setenv("WORK_ORDER_FILE", str(tmp_path / "wo.json"))
    get_settings.cache_clear()


def test_before_metrics_persist_through_create(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    created = client.post("/api/v1/work-orders", json=_base_payload()).json()
    assert created["before_kwh"] == 137.0
    assert created["before_cop"] == 2.0


def test_unassigned_create_is_pending_confirm(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    payload = _base_payload(assignee_id=None, source_record_id="R-UP-NA")
    created = client.post("/api/v1/work-orders", json=payload).json()
    assert created["status"] == "pending_confirm"
    assert created["status_label"] == "待确认"


def test_submit_computes_rounded_estimate(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    wid = client.post("/api/v1/work-orders", json=_base_payload()).json()["work_order_id"]
    client.patch(f"/api/v1/work-orders/{wid}/accept", json={"operator_id": "worker_ahu"})
    sub = client.patch(
        f"/api/v1/work-orders/{wid}/submit",
        json={
            "operator_id": "worker_ahu",
            "actual_cause": "过滤网堵塞",
            "resolution_note": "清洗过滤网",
            "recovery_confirmed": True,
            "attachment_name": "photo.jpg",
            "attachment_note": "清洗前后对比",
        },
    ).json()
    assert sub["after_is_estimated"] is True
    assert sub["attachment_name"] == "photo.jpg"
    # rounded to at most 2 decimals
    assert sub["after_kwh"] == round(137.0 * 0.78, 2)
    assert round(sub["after_kwh"], 2) == sub["after_kwh"]
    assert sub["after_cop"] == round(2.0 * 1.15, 2)


def test_submit_without_recovery_keeps_baseline(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    wid = client.post("/api/v1/work-orders", json=_base_payload(source_record_id="R-UP-NR")).json()["work_order_id"]
    client.patch(f"/api/v1/work-orders/{wid}/accept", json={"operator_id": "worker_ahu"})
    sub = client.patch(
        f"/api/v1/work-orders/{wid}/submit",
        json={
            "operator_id": "worker_ahu",
            "actual_cause": "未恢复",
            "resolution_note": "需后续跟进",
            "recovery_confirmed": False,
        },
    ).json()
    assert sub["after_is_estimated"] is False
    # not recovered -> no fabricated improvement
    assert sub["after_kwh"] == 137.0


def test_auto_confirm_queue_creates_pending_and_is_idempotent(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    first = client.post("/api/v1/work-orders/auto-confirm-queue")
    assert first.status_code == 200
    body = first.json()
    assert body["created_count"] >= 1
    for order in body["created"]:
        assert order["status"] == "pending_confirm"
        assert order["before_kwh"] is not None
        assert order["before_cop"] is not None

    second = client.post("/api/v1/work-orders/auto-confirm-queue").json()
    assert second["created_count"] == 0
    assert second["skipped_count"] >= body["created_count"]


def test_draft_can_be_assigned_and_closed_with_estimate(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    draft = client.post("/api/v1/work-orders/auto-confirm-queue").json()["created"][0]
    wid = draft["work_order_id"]
    assert client.patch(
        f"/api/v1/work-orders/{wid}/assign",
        json={"assignee_id": "worker_ahu", "operator_id": "admin"},
    ).json()["status"] == "assigned"
    client.patch(f"/api/v1/work-orders/{wid}/accept", json={"operator_id": "worker_ahu"})
    client.patch(
        f"/api/v1/work-orders/{wid}/submit",
        json={"operator_id": "worker_ahu", "actual_cause": "a", "resolution_note": "b", "recovery_confirmed": True},
    )
    closed = client.patch(
        f"/api/v1/work-orders/{wid}/review",
        json={"operator_id": "admin", "approved": True},
    ).json()
    assert closed["status"] == "closed"
    assert closed["after_is_estimated"] is True


def test_operation_report_closed_cases_use_estimate_wording(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    wid = client.post("/api/v1/work-orders", json=_base_payload()).json()["work_order_id"]
    client.patch(f"/api/v1/work-orders/{wid}/accept", json={"operator_id": "worker_ahu"})
    client.patch(
        f"/api/v1/work-orders/{wid}/submit",
        json={"operator_id": "worker_ahu", "actual_cause": "a", "resolution_note": "b", "recovery_confirmed": True},
    )
    client.patch(f"/api/v1/work-orders/{wid}/review", json={"operator_id": "admin", "approved": True})

    rep = client.get("/api/v1/analytics/operation-report").json()["item"]
    cases = rep["closed_cases"]
    assert len(cases) >= 1
    case = cases[0]
    assert case["saving_summary"].startswith("预计")
    assert case["cop_summary"].startswith("预计")
    assert case["after_is_estimated"] is True


def test_review_and_accept_state_guards(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    wid = client.post("/api/v1/work-orders", json=_base_payload()).json()["work_order_id"]
    # cannot review before pending_review
    assert client.patch(
        f"/api/v1/work-orders/{wid}/review",
        json={"operator_id": "admin", "approved": True},
    ).status_code == 409
    # drive to closed
    client.patch(f"/api/v1/work-orders/{wid}/accept", json={"operator_id": "worker_ahu"})
    client.patch(
        f"/api/v1/work-orders/{wid}/submit",
        json={"operator_id": "worker_ahu", "actual_cause": "a", "resolution_note": "b", "recovery_confirmed": True},
    )
    client.patch(f"/api/v1/work-orders/{wid}/review", json={"operator_id": "admin", "approved": True})
    # cannot accept a closed order
    assert client.patch(
        f"/api/v1/work-orders/{wid}/accept", json={"operator_id": "worker_ahu"}
    ).status_code == 409
