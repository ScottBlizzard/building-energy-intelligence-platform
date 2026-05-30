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
        "status": "处理中",
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
        "note": "测试工单",
    }
    created = client.post("/api/v1/work-orders", json=payload)
    assert created.status_code == 200
    work_order_id = created.json()["work_order_id"]

    listed = client.get("/api/v1/work-orders")
    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 1

    updated = client.patch(
        f"/api/v1/work-orders/{work_order_id}",
        json={"status": "已完成", "note": "已现场确认"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "已完成"
    assert updated.json()["note"] == "已现场确认"
