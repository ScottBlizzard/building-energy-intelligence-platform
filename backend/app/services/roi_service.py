from __future__ import annotations

from typing import Dict, List

from app.services import simulation_service
from app.services.analysis_service import _add_operational_dimensions, _safe_divide
from app.services.data_loader import get_visible_dataset

_ELECTRICITY_PRICE_YUAN_PER_KWH = 0.82
_ANNUAL_DISCOUNT_RATE = 0.05


_EQUIPMENT_BASELINE = {
    "冷水机组": {
        "typical_power_kw": 350,
        "annual_runtime_h": 3200,
        "typical_lifespan_years": 15,
        "typical_replacement_cost": 350000,
        "typical_vfd_cost": 80000,
    },
    "冷却塔": {
        "typical_power_kw": 45,
        "annual_runtime_h": 2800,
        "typical_lifespan_years": 12,
        "typical_replacement_cost": 120000,
        "typical_vfd_cost": 30000,
    },
    "空气处理机组": {
        "typical_power_kw": 55,
        "annual_runtime_h": 3500,
        "typical_lifespan_years": 15,
        "typical_replacement_cost": 180000,
        "typical_vfd_cost": 45000,
    },
    "风机盘管": {
        "typical_power_kw": 2.5,
        "annual_runtime_h": 4000,
        "typical_lifespan_years": 10,
        "typical_replacement_cost": 8000,
        "typical_vfd_cost": 3000,
    },
}

_RETROFIT_OPTIONS = {
    "变频改造": {"cost_per_kw": 1200, "saving_pct": 0.20, "lifespan": 12},
    "高效设备更换": {"cost_per_kw": 3500, "saving_pct": 0.35, "lifespan": 15},
    "智能控制升级": {"cost_per_kw": 800, "saving_pct": 0.12, "lifespan": 8},
    "综合节能方案": {"cost_per_kw": 2500, "saving_pct": 0.28, "lifespan": 14},
}


def _get_enriched_frame(frame):
    enriched = _add_operational_dimensions(frame)
    return enriched


def _operational_frame():
    return get_visible_dataset()


def _building_equipment_stats(frame, building_id: str, equipment_type: str) -> Dict:
    enriched = _get_enriched_frame(frame)
    subset = enriched[(enriched["building_id"] == building_id) & (enriched["equipment_type"] == equipment_type)]
    if subset.empty:
        return {"equipment_count": 0, "total_kwh": 0, "avg_cop": 0, "anomaly_count": 0}

    observed_kwh = float(subset["electricity_kwh"].sum())
    observed_days = max(1, int(subset["timestamp"].dt.normalize().nunique()))
    annualization_factor = 365 / observed_days
    annual_kwh = observed_kwh * annualization_factor
    hvac = float(subset["hvac_kwh"].sum()) if "hvac_kwh" in subset.columns else 0
    cooling = float(subset["cooling_load_kwh"].sum()) if "cooling_load_kwh" in subset.columns else 0
    avg_cop = round(_safe_divide(cooling, hvac), 2)
    anomaly_count = int(subset["is_anomaly"].sum()) if "is_anomaly" in subset.columns else 0
    equipment_count = int(subset["equipment_id"].nunique())

    return {
        "equipment_count": equipment_count,
        "total_kwh": round(annual_kwh, 2),
        "observed_kwh": round(observed_kwh, 2),
        "observed_days": observed_days,
        "annualization_factor": round(annualization_factor, 2),
        "avg_cop": avg_cop,
        "anomaly_count": anomaly_count,
        "building_name": str(subset["building_name"].iloc[0]) if not subset.empty else building_id,
    }


def _npv(initial_investment: float, annual_saving: float, lifespan: int, discount_rate: float = _ANNUAL_DISCOUNT_RATE) -> float:
    total = -initial_investment
    for year in range(1, lifespan + 1):
        total += annual_saving / ((1 + discount_rate) ** year)
    return round(total, 2)


def _irr(initial_investment: float, annual_saving: float, lifespan: int) -> float:
    if initial_investment <= 0:
        return 999.0

    lo, hi = 0.0, 2.0
    for _ in range(60):
        mid = (lo + hi) / 2
        npv_val = -initial_investment
        for year in range(1, lifespan + 1):
            npv_val += annual_saving / ((1 + mid) ** year)
        if npv_val > 0:
            lo = mid
        else:
            hi = mid

    result = round((lo + hi) / 2 * 100, 1)
    return min(result, 200.0)


def _payback_years(initial_investment: float, annual_saving: float) -> float:
    if annual_saving <= 0:
        return 999.0
    return round(initial_investment / annual_saving, 1)


def _payback_label(payback: float, lifespan: int) -> str:
    if payback >= 999 or payback > lifespan:
        return "寿命期内无法回本"
    return f"{payback} 年"


def _sensitivity_cases(payload: Dict, base_saving_pct: float) -> List[Dict]:
    cases = [
        ("保守", max(0.01, base_saving_pct * 0.75)),
        ("基准", max(0.01, base_saving_pct)),
        ("乐观", min(0.75, base_saving_pct * 1.25)),
    ]
    results = []
    for label, saving_pct in cases:
        case_payload = dict(payload)
        case_payload["expected_saving_pct"] = saving_pct
        result = analyze_roi_project(case_payload, include_sensitivity=False)
        results.append(
            {
                "case": label,
                "expected_saving_pct": result["expected_saving_pct"],
                "annual_saving_yuan": result["annual_saving_yuan"],
                "npv_yuan": result["npv_yuan"],
                "payback_years": result["payback_years"],
                "payback_label": result["payback_label"],
                "assessment": result["assessment"],
            }
        )
    return results


def build_equipment_audit(building_id: str) -> Dict:
    frame = _operational_frame()
    enriched = _get_enriched_frame(frame)
    equipment_types = sorted(enriched["equipment_type"].dropna().unique().tolist())
    results = []

    for eq_type in equipment_types:
        stats = _building_equipment_stats(frame, building_id, eq_type)
        baseline = _EQUIPMENT_BASELINE.get(eq_type, {"typical_power_kw": 30, "annual_runtime_h": 3000, "typical_cop": 2.5, "typical_lifespan_years": 12})
        annual_kwh = stats["total_kwh"]
        annual_cost = round(annual_kwh * _ELECTRICITY_PRICE_YUAN_PER_KWH, 2)
        cop_status = "低效" if stats["avg_cop"] < 2.4 else "正常" if stats["avg_cop"] < 3.0 else "高效"

        results.append(
            {
                "equipment_type": eq_type,
                **stats,
                "annual_cost_yuan": annual_cost,
                "cop_status": cop_status,
                "typical_power_kw": baseline["typical_power_kw"],
                "typical_lifespan_years": baseline["typical_lifespan_years"],
                "retrofit_candidates": _retrofit_candidates(eq_type, stats),
            }
        )

    building_name = str(frame[frame["building_id"] == building_id]["building_name"].iloc[0]) if not frame.empty else building_id
    return {
        "building_id": building_id,
        "building_name": building_name,
        "equipment_list": results,
        "data_scope": "simulation_visible",
        "generated_at": simulation_service.now_str(),
    }


def _retrofit_candidates(equipment_type: str, stats: Dict) -> List[Dict]:
    candidates = []
    baseline = _EQUIPMENT_BASELINE.get(equipment_type, {})
    power_kw = baseline.get("typical_power_kw", 30)
    annual_runtime = baseline.get("annual_runtime_h", 3000)
    annual_kwh = max(float(stats.get("total_kwh", 0)), power_kw * annual_runtime)
    annual_cost = annual_kwh * _ELECTRICITY_PRICE_YUAN_PER_KWH

    for option_name, option_params in _RETROFIT_OPTIONS.items():
        investment = power_kw * option_params["cost_per_kw"]
        saving_pct = option_params["saving_pct"]
        lifespan = option_params["lifespan"]
        annual_saving = annual_cost * saving_pct

        candidates.append(
            {
                "option": option_name,
                "investment_yuan": round(investment, 2),
                "annual_saving_yuan": round(annual_saving, 2),
                "saving_pct": round(saving_pct * 100, 0),
                "lifespan_years": lifespan,
                "npv_yuan": _npv(investment, annual_saving, lifespan),
                "irr_pct": _irr(investment, annual_saving, lifespan),
                "payback_years": _payback_years(investment, annual_saving),
            }
        )

    return sorted(candidates, key=lambda c: c["npv_yuan"], reverse=True)


def analyze_roi_project(payload: Dict, include_sensitivity: bool = True) -> Dict:
    building_id = payload["building_id"]
    equipment_type = payload["equipment_type"]
    investment = float(payload["investment_yuan"])
    expected_saving_pct = float(payload.get("expected_saving_pct") or 0.20)
    annual_maintenance = float(payload.get("annual_maintenance_cost") or 0)

    frame = _operational_frame()
    stats = _building_equipment_stats(frame, building_id, equipment_type)
    annual_kwh = stats["total_kwh"]
    annual_cost = annual_kwh * _ELECTRICITY_PRICE_YUAN_PER_KWH

    if expected_saving_pct < 0.01:
        baseline = _EQUIPMENT_BASELINE.get(equipment_type, {})
        power_kw = baseline.get("typical_power_kw", 30)
        runtime = baseline.get("annual_runtime_h", 3000)
        annual_kwh = power_kw * runtime * stats.get("equipment_count", 1)
        annual_cost = annual_kwh * _ELECTRICITY_PRICE_YUAN_PER_KWH

    annual_saving = annual_cost * expected_saving_pct - annual_maintenance
    if annual_saving <= 0:
        annual_saving = annual_cost * 0.15

    lifespan_map = {"冷水机组": 15, "冷却塔": 12, "空气处理机组": 15, "风机盘管": 10}
    lifespan = int(payload.get("project_lifespan_years") or lifespan_map.get(equipment_type, 12))

    npv_val = _npv(investment, annual_saving, lifespan)
    irr_val = _irr(investment, annual_saving, lifespan)
    payback = _payback_years(investment, annual_saving)
    payback_within_lifespan = payback < 999 and payback <= lifespan

    assessment = "强烈推荐"
    if npv_val < 0:
        assessment = "不推荐"
    elif not payback_within_lifespan:
        assessment = "不推荐"
    elif payback > 5:
        assessment = "谨慎推荐"
    elif payback > 3:
        assessment = "推荐"

    result = {
        "project_name": payload.get("project_name") or f"{equipment_type}节能改造项目",
        "building_id": building_id,
        "building_name": stats.get("building_name", building_id),
        "equipment_type": equipment_type,
        "investment_yuan": investment,
        "annual_saving_yuan": round(annual_saving, 2),
        "annual_saving_kwh": round(annual_saving / _ELECTRICITY_PRICE_YUAN_PER_KWH, 2),
        "expected_saving_pct": round(expected_saving_pct * 100, 1),
        "project_lifespan_years": lifespan,
        "npv_yuan": npv_val,
        "irr_pct": irr_val,
        "payback_years": payback,
        "payback_label": _payback_label(payback, lifespan),
        "payback_within_lifespan": payback_within_lifespan,
        "assessment": assessment,
        "current_annual_kwh": round(annual_kwh, 2),
        "current_annual_cost_yuan": round(annual_cost, 2),
        "roi_5year_pct": round(_safe_divide(annual_saving * 5 - investment, investment) * 100, 1),
        "carbon_reduction_kg_per_year": round(annual_saving / _ELECTRICITY_PRICE_YUAN_PER_KWH * 0.5703, 2),
        "observed_days": stats.get("observed_days", 0),
        "annualization_factor": stats.get("annualization_factor", 0),
        "data_scope": "simulation_visible",
        "generated_at": simulation_service.now_str(),
    }
    if include_sensitivity:
        result["sensitivity"] = _sensitivity_cases(payload, expected_saving_pct)
    return result


def compare_scenarios(payload: Dict) -> Dict:
    scenarios = payload.get("scenarios", [])
    if not scenarios:
        return {"scenarios": [], "comparison": {}, "recommendation": ""}

    results = [analyze_roi_project(s.model_dump() if hasattr(s, "model_dump") else s) for s in scenarios]

    best = max(results, key=lambda r: r["npv_yuan"])
    feasible = [r for r in results if r.get("payback_within_lifespan")]
    fastest = min(feasible or results, key=lambda r: r["payback_years"])

    return {
        "scenarios": results,
        "comparison": {
            "best_npv": {"name": best["project_name"], "npv_yuan": best["npv_yuan"]},
            "fastest_payback": {
                "name": fastest["project_name"],
                "payback_years": fastest["payback_years"],
                "payback_label": fastest["payback_label"],
            },
            "feasible_count": len(feasible),
            "scenario_count": len(results),
            "investment_range": {
                "min": round(min(r["investment_yuan"] for r in results), 2),
                "max": round(max(r["investment_yuan"] for r in results), 2),
            },
        },
        "recommendation": (
            f"综合经济性分析，建议优先实施「{best['project_name']}」，"
            f"NPV={best['npv_yuan']:,.0f}元，回收期{best['payback_label']}，"
            f"5年ROI={best['roi_5year_pct']}%。"
            if best["npv_yuan"] > 0
            else "当前方案均不具备经济可行性，建议降低投资成本或提高预期节能率后重新评估。"
        ),
        "generated_at": simulation_service.now_str(),
    }
