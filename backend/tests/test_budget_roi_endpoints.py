from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


client = TestClient(app)


def _is_positive_number(value):
    return isinstance(value, (int, float)) and value > 0


def test_budget_analysis_and_kpi_use_business_metrics(tmp_path, monkeypatch):
    monkeypatch.setenv("BUDGET_FILE", str(tmp_path / "budgets.json"))
    get_settings.cache_clear()

    analysis_response = client.get(
        "/api/v1/budget/budgets/analysis",
        params={"year": 2026, "month": 5},
    )
    assert analysis_response.status_code == 200
    analysis = analysis_response.json()["item"]
    assert _is_positive_number(analysis["total_budget_kwh"])
    assert "total_projected_execution_rate" in analysis
    assert analysis["buildings"]
    assert "month_end_estimate_kwh" in analysis["buildings"][0]
    assert "projected_execution_rate" in analysis["buildings"][0]

    building_id = analysis["buildings"][0]["building_id"]
    kpi_response = client.get(
        f"/api/v1/budget/budgets/kpi/{building_id}",
        params={"year": 2026},
    )
    assert kpi_response.status_code == 200
    kpi = kpi_response.json()["item"]
    assert "cop_pass_rate" in kpi
    assert "budget_control_rate" in kpi
    assert "anomaly_response_timely_rate" in kpi
    assert "score_breakdown" in kpi
    assert kpi["monthly_details"]
    assert "projected_execution_rate" in kpi["monthly_details"][0]
    assert "anomaly_response_timely_rate" in kpi["monthly_details"][0]
    assert "score_breakdown" in kpi["monthly_details"][0]
    assert "score_reasons" in kpi["monthly_details"][0]


def test_roi_audit_and_analysis_support_clean_and_legacy_routes():
    audit_response = client.get("/api/v1/roi/audit/BLD-C")
    assert audit_response.status_code == 200
    audit = audit_response.json()["item"]
    assert audit["building_id"] == "BLD-C"
    assert audit["equipment_list"]
    assert "observed_days" in audit["equipment_list"][0]
    assert audit["equipment_list"][0]["retrofit_candidates"]

    legacy_response = client.get("/api/v1/roi/roi/audit/BLD-C")
    assert legacy_response.status_code == 200

    roi_response = client.post(
        "/api/v1/roi/analyze",
        json={
            "building_id": "BLD-C",
            "equipment_type": "冷水机组",
            "investment_yuan": 120000,
            "expected_saving_pct": 0.2,
            "project_lifespan_years": 12,
            "annual_maintenance_cost": 3000,
        },
    )
    assert roi_response.status_code == 200
    roi = roi_response.json()["item"]
    assert roi["project_lifespan_years"] == 12
    assert _is_positive_number(roi["annual_saving_yuan"])
    assert "payback_years" in roi
    assert "payback_label" in roi
    assert "payback_within_lifespan" in roi
    assert "npv_yuan" in roi
    assert "irr_pct" in roi
    assert "sensitivity" in roi
    assert len(roi["sensitivity"]) == 3


def test_roi_compare_returns_multi_scenario_recommendation():
    response = client.post(
        "/api/v1/roi/compare",
        json={
            "building_id": "BLD-C",
            "scenarios": [
                {
                    "building_id": "BLD-C",
                    "equipment_type": "冷水机组",
                    "project_name": "策略调优",
                    "investment_yuan": 50000,
                    "expected_saving_pct": 0.12,
                    "project_lifespan_years": 8,
                },
                {
                    "building_id": "BLD-C",
                    "equipment_type": "冷水机组",
                    "project_name": "设备更换",
                    "investment_yuan": 350000,
                    "expected_saving_pct": 0.35,
                    "project_lifespan_years": 15,
                },
            ],
        },
    )
    assert response.status_code == 200
    item = response.json()["item"]
    assert len(item["scenarios"]) == 2
    assert item["comparison"]["scenario_count"] == 2
    assert "payback_label" in item["comparison"]["fastest_payback"]
    assert item["recommendation"]
