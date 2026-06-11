"""L2 ROI 重构验收测试（对照 docs/28 §6）。

断言尽量基于"性质/口径"而非硬编码数值，避免随数据微调而脆断。
"""
from app.services.data_loader import clear_dataset_cache
from app.services import roi_service


def setup_function(_):
    clear_dataset_cache()


def test_audit_scoped_to_building_and_no_fake_low_eff():
    audit = roi_service.build_equipment_audit("BLD-A")
    assert audit["equipment_list"]
    for eq in audit["equipment_list"]:
        # COP=0（无制冷数据）不得判“低效”。
        if eq["avg_cop"] <= 0:
            assert eq["cop_status"] == "无数据"
        # 有实测数据才产出改造方案；无数据则方案为空且带说明。
        if eq["has_real_data"]:
            assert eq["retrofit_candidates"]
        else:
            assert eq["retrofit_candidates"] == []
            assert eq["data_note"]


def test_candidates_have_eaa_and_no_zero_year_payback():
    audit = roi_service.build_equipment_audit("BLD-C")
    eq = next(e for e in audit["equipment_list"] if e["has_real_data"])
    for cand in eq["retrofit_candidates"]:
        assert "eaa_yuan" in cand
        assert "discounted_payback_years" in cand
        assert cand["saving_basis"]
        assert cand["investment_basis"]
        # 不再出现 0 / 0.1 年的回收期（要么>=1，要么 999 表示不回本）。
        pb = cand["discounted_payback_years"]
        assert pb >= 1.0 or pb >= 999.0


def test_no_fabricated_saving_when_uneconomic():
    # 极小节能率 + 巨额维护 → 年净节省 ≤ 0，必须如实“不推荐”，不得强塞收益。
    result = roi_service.analyze_roi_project(
        {
            "building_id": "BLD-C",
            "equipment_type": "冷水机组",
            "investment_yuan": 500000,
            "expected_saving_pct": 0.01,
            "annual_maintenance_cost": 999999,
            "project_lifespan_years": 12,
        }
    )
    assert result["annual_saving_yuan"] <= 0
    assert result["assessment"] == "不推荐"
    assert result["npv_yuan"] < 0


def test_discount_rate_sensitivity_is_monotonic():
    result = roi_service.analyze_roi_project(
        {
            "building_id": "BLD-C",
            "equipment_type": "冷水机组",
            "investment_yuan": 120000,
            "expected_saving_pct": 0.2,
            "project_lifespan_years": 12,
            "annual_maintenance_cost": 3000,
        }
    )
    sens = result["sensitivity"]
    assert len(sens) == 3
    npvs = [s["npv_yuan"] for s in sens]  # 5% / 8% / 10%
    assert npvs[0] >= npvs[1] >= npvs[2]
    assert result["eaa_yuan"] != 0.0
    assert result["discount_rate"] == 8.0


def test_compare_ranks_by_eaa_among_feasible():
    payload = {
        "building_id": "BLD-C",
        "scenarios": [
            {
                "building_id": "BLD-C",
                "equipment_type": "冷水机组",
                "project_name": "短寿命方案",
                "investment_yuan": 40000,
                "expected_saving_pct": 0.10,
                "project_lifespan_years": 8,
            },
            {
                "building_id": "BLD-C",
                "equipment_type": "冷水机组",
                "project_name": "长寿命方案",
                "investment_yuan": 120000,
                "expected_saving_pct": 0.20,
                "project_lifespan_years": 15,
            },
        ],
    }
    result = roi_service.compare_scenarios(payload)
    assert "best_eaa" in result["comparison"]
    best_name = result["comparison"]["best_eaa"]["name"]
    feasible = [s for s in result["scenarios"] if s["npv_yuan"] > 0 and s["payback_within_lifespan"]]
    if feasible:
        assert best_name == max(feasible, key=lambda s: s["eaa_yuan"])["project_name"]
