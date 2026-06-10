from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _payload(**overrides):
    data = {
        "source_record_id": "R-GROUND-1",
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
        "before_kwh": 150.0,
        "before_cop": 2.0,
        "risk_score": 88.0,
        "wasted_kwh": 30.0,
        "wasted_cost_yuan": 24.6,
        "estimated_saving_yuan": 18.45,
        "carbon_kg": 17.11,
        "sla_hours": 8,
    }
    data.update(overrides)
    return data


def _closed_order():
    created = client.post("/api/v1/work-orders", json=_payload()).json()
    wid = created["work_order_id"]
    client.patch(f"/api/v1/work-orders/{wid}/accept", json={"operator_id": "worker_ahu"})
    client.patch(
        f"/api/v1/work-orders/{wid}/submit",
        json={
            "operator_id": "worker_ahu",
            "actual_cause": "过滤网堵塞",
            "resolution_note": "已清洗并恢复自动控制",
            "recovery_confirmed": True,
        },
    )
    return client.patch(
        f"/api/v1/work-orders/{wid}/review",
        json={"operator_id": "admin", "approved": True},
    ).json()


def test_work_order_question_uses_realtime_grounding():
    closed = _closed_order()
    response = client.post("/api/v1/assistant/query", json={"question": "刚关闭的工单是什么？"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["grounding_used"] is True
    assert payload["grounding_status"] == "grounded"
    assert closed["work_order_id"] in payload["answer"]
    assert closed["equipment_id"] in payload["answer"]
    assert "work_orders" in payload["grounding_sources"]


def test_invalid_external_work_order_answer_falls_back(monkeypatch):
    closed = _closed_order()

    def fake_external(*args, **kwargs):
        return {"answer": "刚关闭的是 WO-FAKE-999，设备 AHU-Z-9F-99。", "provider": "fake", "model": "fake"}

    monkeypatch.setattr("app.api.routes.assistant.build_external_assistant_answer", fake_external)

    response = client.post("/api/v1/assistant/query", json={"question": "刚关闭的工单是什么？"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["llm_used"] is False
    assert payload["grounding_status"] == "fallback_after_validation"
    assert payload["validation_warnings"]
    assert "WO-FAKE-999" not in payload["answer"]
    assert closed["work_order_id"] in payload["answer"]


def test_decision_endpoints_rank_dispatch_and_budget_impact():
    closed = _closed_order()
    client.post(
        "/api/v1/work-orders",
        json=_payload(
            source_record_id="R-GROUND-2",
            work_order_id="WO-LOW-TEST",
            equipment_id="FCU-C-4F-02",
            equipment_type="风机盘管",
            priority="中",
            risk_score=45,
            wasted_cost_yuan=5,
            estimated_saving_yuan=3,
            carbon_kg=2,
            sla_hours=72,
        ),
    )

    priorities = client.get("/api/v1/decisions/work-order-priorities", params={"limit": 5}).json()["items"]
    assert priorities
    assert priorities[0]["decision_score"] >= priorities[-1]["decision_score"]
    assert "score_breakdown" in priorities[0]

    plan = client.get("/api/v1/decisions/dispatch-plan", params={"worker_capacity": 1}).json()["item"]
    assert len(plan["selected"]) == 1
    assert plan["summary"]

    impact = client.get("/api/v1/decisions/budget-impact", params={"year": 2026, "month": 5}).json()["item"]
    assert impact["closed_order_count"] >= 1
    assert impact["total_saved_kwh"] > 0
    assert impact["budget_projection"]
    assert closed["building_id"] in {item["building_id"] for item in impact["buildings"]}


def test_roi_candidates_and_counterfactual_scenarios():
    _closed_order()
    client.post(
        "/api/v1/work-orders",
        json=_payload(source_record_id="R-GROUND-3", work_order_id="WO-REPEAT-TEST"),
    )

    candidates = client.get("/api/v1/decisions/roi-candidates", params={"limit": 5}).json()["items"]
    assert candidates
    assert any(item["equipment_id"] == "AHU-C-4F-06" for item in candidates)
    assert "recommended_option" in candidates[0]

    response = client.post(
        "/api/v1/sim/counterfactual",
        json={"equipment_id": "AHU-C-4F-06", "start_date": "2026-05-01", "horizon_days": 7, "delay_days": 3},
    )
    assert response.status_code == 200
    item = response.json()["item"]
    assert len(item["scenarios"]) == 3
    assert {scenario["key"] for scenario in item["scenarios"]} == {"no_action", "immediate", "delayed"}
    assert item["decision_sentence"]


def test_role_permissions_for_admin_and_worker_boundaries():
    wid = client.post("/api/v1/work-orders", json=_payload()).json()["work_order_id"]

    forbidden_review = client.patch(
        f"/api/v1/work-orders/{wid}/review",
        json={"operator_id": "worker_ahu", "approved": True},
    )
    assert forbidden_review.status_code == 403

    forbidden_budget = client.get(
        "/api/v1/budget/budgets/analysis",
        params={"year": 2026, "month": 5, "operator_id": "worker_ahu"},
    )
    assert forbidden_budget.status_code == 403

    forbidden_roi = client.get("/api/v1/roi/audit/BLD-C", params={"operator_id": "worker_ahu"})
    assert forbidden_roi.status_code == 403

    accepted = client.patch(f"/api/v1/work-orders/{wid}/accept", json={"operator_id": "worker_ahu"})
    assert accepted.status_code == 200
