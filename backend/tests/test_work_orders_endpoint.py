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


def _ahu_payload(record_id, equipment_id):
    return {
        "source_record_id": record_id,
        "priority": "高",
        "building_id": "BLD-C",
        "building_name": "图书信息楼C",
        "floor_label": "4F",
        "zone_name": "阅读区",
        "equipment_id": equipment_id,
        "equipment_type": "空气处理机组",
        "timestamp": "2026-05-01 10:00:00",
        "anomaly_reason": "电耗高于同时段基线",
        "possible_cause": "新风阀卡滞",
        "recommended_action": "复位风阀",
        "owner_role": "空调系统运维员",
        "assignee_id": "worker_ahu",
    }


def test_busy_worker_cannot_take_second_active_order(tmp_path, monkeypatch):
    monkeypatch.setenv("WORK_ORDER_FILE", str(tmp_path / "work_orders.json"))
    get_settings.cache_clear()

    first = client.post("/api/v1/work-orders", json=_ahu_payload("R-BUSY-1", "AHU-C-4F-01"))
    assert first.status_code == 200
    assert first.json()["status"] == "assigned"

    # 同一工人忙碌期间再派第二单 -> 409 且返回明确占用信息
    second = client.post("/api/v1/work-orders", json=_ahu_payload("R-BUSY-2", "AHU-C-4F-02"))
    assert second.status_code == 409
    assert "正在处理工单" in second.json()["detail"]

    # 工人提交完工后转为空闲，可以再接单
    wid = first.json()["work_order_id"]
    client.patch(f"/api/v1/work-orders/{wid}/accept", json={"operator_id": "worker_ahu"})
    client.patch(
        f"/api/v1/work-orders/{wid}/submit",
        json={"operator_id": "worker_ahu", "actual_cause": "a", "resolution_note": "b", "recovery_confirmed": True},
    )
    third = client.post("/api/v1/work-orders", json=_ahu_payload("R-BUSY-3", "AHU-C-4F-03"))
    assert third.status_code == 200
    assert third.json()["status"] == "assigned"
