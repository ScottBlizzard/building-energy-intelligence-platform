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


def test_same_equipment_cannot_be_dispatched_twice(tmp_path, monkeypatch):
    """设备级去重：同一台设备已有未关闭工单时，针对它其它异常再派单应被拒绝。"""
    monkeypatch.setenv("WORK_ORDER_FILE", str(tmp_path / "work_orders.json"))
    get_settings.cache_clear()

    first = client.post("/api/v1/work-orders", json=_ahu_payload("R-EQ-1", "AHU-C-4F-09"))
    assert first.status_code == 200

    # 同一设备、另一条异常读数 -> 409，且提示是“同设备已有未关闭工单”而非工人忙碌。
    second = client.post("/api/v1/work-orders", json=_ahu_payload("R-EQ-2", "AHU-C-4F-09"))
    assert second.status_code == 409
    assert "已有未关闭工单" in second.json()["detail"]


def test_repaired_equipment_blocks_new_order_and_closes_siblings(tmp_path, monkeypatch):
    """关单（修复整台设备）后：不能再对该设备派新单；同设备其它未关闭工单联动关闭。"""
    monkeypatch.setenv("WORK_ORDER_FILE", str(tmp_path / "work_orders.json"))
    get_settings.cache_clear()

    from app.services import work_order_store as store

    equipment_id = "FCU-D-3F-06"
    # 直接在存储层埋入同一设备的两张未关闭工单（模拟历史/导入数据），验证联动关闭。
    store._write_orders([
        {
            "work_order_id": "WO-MAIN",
            "source_record_id": "R-MAIN",
            "equipment_id": equipment_id,
            "equipment_type": "风机盘管",
            "building_id": "BLD-D",
            "status": "pending_review",
            "assignee_id": "worker_fcu",
            "priority": "高",
        },
        {
            "work_order_id": "WO-SIBLING",
            "source_record_id": "R-SIB",
            "equipment_id": equipment_id,
            "equipment_type": "风机盘管",
            "building_id": "BLD-D",
            "status": "pending_confirm",
            "priority": "中",
        },
    ])

    reviewed = client.patch(
        "/api/v1/work-orders/WO-MAIN/review",
        json={"operator_id": "admin", "approved": True, "review_note": "修复完成"},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["status"] == "closed"

    # 同设备的其它未关闭工单被联动关闭。
    sibling = next(o for o in store.list_work_orders() if o["work_order_id"] == "WO-SIBLING")
    assert sibling["status"] == "closed"
    assert sibling["verification_status"] == "随同设备修复关闭"

    # 设备已修复，再对它派新单 -> 409，提示已完成维修。
    blocked = client.post("/api/v1/work-orders", json={
        "source_record_id": "R-AFTER",
        "priority": "高",
        "building_id": "BLD-D",
        "building_name": "实训楼D",
        "floor_label": "3F",
        "zone_name": "实训区",
        "equipment_id": equipment_id,
        "equipment_type": "风机盘管",
        "timestamp": "2026-05-02 10:00:00",
        "anomaly_reason": "电耗高于同时段基线",
        "possible_cause": "末端阀门卡滞",
        "recommended_action": "现场复位末端阀门",
        "owner_role": "空调系统运维员",
        "assignee_id": "worker_fcu",
    })
    assert blocked.status_code == 409
    assert "完成维修" in blocked.json()["detail"]
