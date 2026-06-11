"""Tests for the operational sandbox simulation clock ("time machine")."""
import pandas as pd
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.services import simulation_service
from app.services.analysis_service import build_analysis_frame, build_anomaly_summary
from app.services.data_loader import get_visible_dataset, read_dataset

client = TestClient(app)


def _isolate(tmp_path, monkeypatch):
    monkeypatch.setenv("WORK_ORDER_FILE", str(tmp_path / "wo.json"))
    get_settings.cache_clear()
    simulation_service.reset()


def test_inactive_by_default_returns_full_dataset(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    assert simulation_service.is_active() is False
    assert len(get_visible_dataset()) == len(read_dataset())


def test_window_hides_future(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    full_max = read_dataset()["timestamp"].max()

    simulation_service.start_simulation("2026-04-01")
    visible = get_visible_dataset()
    assert visible["timestamp"].max() <= pd.Timestamp("2026-04-01 23:59:59")
    assert visible["timestamp"].max() < full_max
    assert len(visible) < len(read_dataset())


def test_advance_reveals_more_data(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    simulation_service.start_simulation("2026-04-01")
    before = len(get_visible_dataset())
    simulation_service.advance_day(15)
    after = len(get_visible_dataset())
    assert after > before


def test_intervention_recovers_equipment(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    # full window so every anomaly is visible
    simulation_service.start_simulation("2026-06-02")

    anomalies = build_anomaly_summary(build_analysis_frame(get_visible_dataset()))
    assert anomalies, "expected some anomalies in the full window"
    # pick the equipment with the most anomalies as the control subject
    counts: dict = {}
    for item in anomalies:
        counts[item["equipment_id"]] = counts.get(item["equipment_id"], 0) + 1
    target = max(counts, key=counts.get)
    assert counts[target] >= 1

    # repair it for the entire timeline (dataset now starts 2026-01-01)
    simulation_service.register_intervention(target, from_date="2026-01-01")

    after = build_anomaly_summary(build_analysis_frame(get_visible_dataset()))
    remaining = [a for a in after if a["equipment_id"] == target]
    assert remaining == [], f"{target} should have recovered after intervention"


def test_future_keeps_producing_new_anomalies(tmp_path, monkeypatch):
    """Even if every equipment failing today is repaired, advancing the clock must
    still surface fresh anomalies on equipment that previously looked healthy, while
    repaired equipment never re-fails after its repair date."""
    _isolate(tmp_path, monkeypatch)
    simulation_service.start_simulation("2026-05-01")

    def anomalies_on(day_str):
        rows = build_anomaly_summary(build_analysis_frame(get_visible_dataset()))
        return {a["equipment_id"] for a in rows if str(a["timestamp"]).startswith(day_str)}

    def anomalies_from(day_str):
        rows = build_anomaly_summary(build_analysis_frame(get_visible_dataset()))
        return [a for a in rows if str(a["timestamp"]) >= day_str]

    repaired = anomalies_on("2026-05-01")
    assert repaired, "expected anomalies on the first day"

    # "fix everything failing today", effective from today onward
    for equipment_id in repaired:
        simulation_service.register_intervention(equipment_id, from_date="2026-05-01")

    fresh_equipment = set()
    for _ in range(20):
        state = simulation_service.advance_day(1)
        today = state["current_date"]
        # brand-new failures = equipment failing today that we did NOT repair on day 1
        fresh_equipment |= (anomalies_on(today) - repaired)
        if fresh_equipment:
            break

    assert fresh_equipment, "advancing the clock never produced a brand-new anomaly"

    # repaired equipment must have zero anomalies dated on/after its repair date
    lingering = [a for a in anomalies_from("2026-05-01") if a["equipment_id"] in repaired]
    assert lingering == [], f"repaired equipment re-failed after repair: {lingering[:3]}"

    # a freshly-failed equipment can itself be repaired and then stays fixed
    target = next(iter(fresh_equipment))
    repair_day = str(simulation_service.get_current_date())
    simulation_service.register_intervention(target, from_date=repair_day)
    simulation_service.advance_day(1)
    post = [a for a in anomalies_from(repair_day) if a["equipment_id"] == target]
    assert post == [], f"{target} re-failed after being repaired: {post[:3]}"


def test_sim_endpoints_roundtrip(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)

    state = client.get("/api/v1/sim/state").json()
    assert state["active"] is False
    assert "data_range" in state

    started = client.post("/api/v1/sim/start", json={"start_date": "2026-05-01"}).json()
    assert started["active"] is True
    assert started["current_date"] == "2026-05-01"

    advanced = client.post("/api/v1/sim/advance", json={"days": 3}).json()
    assert advanced["current_date"] == "2026-05-04"

    reset = client.post("/api/v1/sim/reset").json()
    assert reset["active"] is False


def test_closing_work_order_registers_intervention(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    simulation_service.start_simulation("2026-05-01")

    payload = {
        "source_record_id": "R-SIM-1",
        "priority": "高",
        "building_id": "BLD-C",
        "building_name": "图书信息楼C",
        "floor_label": "4F",
        "zone_name": "阅读区",
        "equipment_id": "AHU-C-4F-06",
        "equipment_type": "空气处理机组",
        "timestamp": "2026-05-01 10:00:00",
        "anomaly_reason": "设备状态异常",
        "possible_cause": "设备告警",
        "recommended_action": "检查 AHU 运行状态",
        "owner_role": "空调系统运维员",
        "assignee_id": "worker_ahu",
    }
    wid = client.post("/api/v1/work-orders", json=payload).json()["work_order_id"]
    client.patch(f"/api/v1/work-orders/{wid}/accept", json={"operator_id": "worker_ahu"})
    client.patch(
        f"/api/v1/work-orders/{wid}/submit",
        json={"operator_id": "worker_ahu", "actual_cause": "a", "resolution_note": "b", "recovery_confirmed": True},
    )
    client.patch(f"/api/v1/work-orders/{wid}/review", json={"operator_id": "admin", "approved": True})

    interventions = simulation_service.get_interventions()
    assert any(i["equipment_id"] == "AHU-C-4F-06" for i in interventions)
    # the repair date should be the simulated "today"
    repair = next(i for i in interventions if i["equipment_id"] == "AHU-C-4F-06")
    assert repair["from_date"] == "2026-05-01"
