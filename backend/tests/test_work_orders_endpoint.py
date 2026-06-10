from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


client = TestClient(app)


def test_persistent_work_order_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setenv("WORK_ORDER_FILE", str(tmp_path / "work_orders.json"))
    get_settings.cache_clear()

    payload = {
        "source_record_id": "R-TEST",
        "priority": "高",
        "building_id": "BLD-A",
        "building_name": "综合教学楼A",
        "floor_label": "RF 屋顶",
        "zone_name": "能源站/设备区",
        "equipment_id": "CT-A-RF-01",
        "equipment_type": "冷却塔",
        "timestamp": "2026-06-01 12:00:00",
        "anomaly_reason": "设备状态异常",
        "possible_cause": "设备告警",
        "recommended_action": "现场复核冷却塔运行状态",
        "owner_role": "制冷机房值班员",
        "assignee_id": "worker_chiller",
        "note": "测试工单",
    }
    created = client.post("/api/v1/work-orders", json=payload)
    assert created.status_code == 200
    created_payload = created.json()
    work_order_id = created_payload["work_order_id"]
    assert created_payload["status"] == "assigned"
    assert created_payload["status_label"] == "已派单"
    assert created_payload["timeline"]

    listed = client.get("/api/v1/work-orders")
    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 1

    accepted = client.patch(
        f"/api/v1/work-orders/{work_order_id}/accept",
        json={"operator_id": "worker_chiller", "note": "已接单"},
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "in_progress"

    submitted = client.patch(
        f"/api/v1/work-orders/{work_order_id}/submit",
        json={
            "operator_id": "worker_chiller",
            "actual_cause": "冷却塔风机告警",
            "resolution_note": "现场复位并检查喷淋状态",
            "recovery_confirmed": True,
        },
    )
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "pending_review"
    assert submitted.json()["actual_cause"] == "冷却塔风机告警"

    reviewed = client.patch(
        f"/api/v1/work-orders/{work_order_id}/review",
        json={"operator_id": "admin", "approved": True, "review_note": "复核通过"},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["status"] == "closed"
    assert reviewed.json()["closed_at"]
    assert len(reviewed.json()["timeline"]) >= 4


def test_worker_can_only_accept_own_order(tmp_path, monkeypatch):
    monkeypatch.setenv("WORK_ORDER_FILE", str(tmp_path / "work_orders.json"))
    get_settings.cache_clear()

    payload = {
        "source_record_id": "R-TEST-2",
        "priority": "中",
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
    }
    work_order_id = client.post("/api/v1/work-orders", json=payload).json()["work_order_id"]

    rejected = client.patch(
        f"/api/v1/work-orders/{work_order_id}/accept",
        json={"operator_id": "worker_chiller"},
    )
    assert rejected.status_code == 409

    accepted = client.patch(
        f"/api/v1/work-orders/{work_order_id}/accept",
        json={"operator_id": "worker_ahu"},
    )
    assert accepted.status_code == 200
