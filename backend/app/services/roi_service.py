from __future__ import annotations

from typing import Dict, List, Optional

from app.services import simulation_service
from app.services.analysis_service import _add_operational_dimensions, _safe_divide
from app.services.data_loader import get_visible_dataset

_ELECTRICITY_PRICE_YUAN_PER_KWH = 0.82  # 工商业目录电价（元/kWh）
_CARBON_KG_PER_KWH = 0.5703  # 全国电网平均碳排因子（生态环境部 2022）

# 基准折现率 = 8%（《建设项目经济评价方法与参数（第三版）》社会折现率）。
_DISCOUNT_RATE = 0.08
_SENSITIVITY_RATES = (0.05, 0.08, 0.10)
_PRICE_ESCALATION = 0.03  # 电价年递增情景（默认 3%/年）
_CARBON_PRICE_YUAN_PER_TON = 80.0  # 全国碳市场参考价（加分情景，非主结论）


# 单台设备口径：典型功率/年运行时数仅用于"数据不足"提示与规模参考；
# target_cop 用于能效差调节；invest 为**增量法**单台投资（见 docs/28 §2.3）：
#   变频/智能/综合 = 改造直接投入（本就是增量）
#   高效设备更换   = 高效型相对标准型的差价（到寿命更换只算差价）
_EQUIPMENT_BASELINE = {
    "冷水机组": {
        "typical_power_kw": 350,
        "annual_runtime_h": 3200,
        "typical_lifespan_years": 15,
        "target_cop": 3.6,
        "invest": {"变频改造": 80000, "高效设备更换": 120000, "智能控制升级": 45000, "综合节能方案": 180000},
    },
    "冷却塔": {
        "typical_power_kw": 45,
        "annual_runtime_h": 2800,
        "typical_lifespan_years": 12,
        "target_cop": 3.2,
        "invest": {"变频改造": 30000, "高效设备更换": 40000, "智能控制升级": 18000, "综合节能方案": 70000},
    },
    "空气处理机组": {
        "typical_power_kw": 55,
        "annual_runtime_h": 3500,
        "typical_lifespan_years": 15,
        "target_cop": 3.4,
        "invest": {"变频改造": 45000, "高效设备更换": 60000, "智能控制升级": 25000, "综合节能方案": 110000},
    },
    "风机盘管": {
        "typical_power_kw": 2.5,
        "annual_runtime_h": 4000,
        "typical_lifespan_years": 10,
        "target_cop": 3.0,
        "invest": {"变频改造": 3000, "高效设备更换": 5000, "智能控制升级": 2500, "综合节能方案": 8000},
    },
}

# base_saving_pct：节能改造措施的基准节能率（取自暖通节能改造经验区间），
# 实际节能率再按当前能效差 efficiency_gap_factor 下调（COP 已达标的设备拿不到满额）。
_RETROFIT_OPTIONS = {
    "变频改造": {"base_saving_pct": 0.20, "lifespan": 12, "investment_basis": "变频改造直接投入（增量）"},
    "高效设备更换": {"base_saving_pct": 0.35, "lifespan": 15, "investment_basis": "高效型相对标准型差价（到寿命更换增量法）"},
    "智能控制升级": {"base_saving_pct": 0.12, "lifespan": 8, "investment_basis": "楼宇控制升级直接投入"},
    "综合节能方案": {"base_saving_pct": 0.28, "lifespan": 14, "investment_basis": "综合改造直接投入"},
}

_SAVING_BASIS = "实测年化电耗 × 措施基准节能率 ×（按当前 COP 能效差调节）"
_LIFESPAN_MAP = {"冷水机组": 15, "冷却塔": 12, "空气处理机组": 15, "风机盘管": 10}


def _get_enriched_frame(frame):
    return _add_operational_dimensions(frame)


def _operational_frame():
    return get_visible_dataset()


def _efficiency_gap_factor(cop_now: float, target_cop: float) -> float:
    """当前能效越差、可挖潜越大；COP 已达标的设备落到下限 0.5（docs/28 §2.2）。"""
    if cop_now <= 0 or target_cop <= 0:
        return 1.0
    gap = (target_cop - cop_now) / target_cop
    return max(0.5, min(1.3, gap))


def _building_equipment_stats(frame, building_id: str, equipment_type: str) -> Dict:
    enriched = _get_enriched_frame(frame)
    subset = enriched[(enriched["building_id"] == building_id) & (enriched["equipment_type"] == equipment_type)]
    if subset.empty:
        return {
            "equipment_count": 0,
            "total_kwh": 0,
            "observed_kwh": 0,
            "observed_days": 0,
            "annualization_factor": 0,
            "avg_cop": 0,
            "anomaly_count": 0,
            "has_real_data": False,
            "building_name": building_id,
        }

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
        "has_real_data": equipment_count > 0 and observed_kwh > 0,
        "building_name": str(subset["building_name"].iloc[0]),
    }


def _cashflows(annual_saving_year1: float, lifespan: int, escalation: float) -> List[float]:
    """逐年净现金流，含电价递增（year1 为基准，之后按 esc 复利增长）。"""
    return [annual_saving_year1 * ((1 + escalation) ** (year - 1)) for year in range(1, lifespan + 1)]


def _cumulative_cashflow_series(initial_investment: float, cashflows: List[float]) -> List[Dict]:
    """累计（未折现）净现金流序列：Y0 起从 -投资 起步，逐年加回净节省。

    用于前端现金流图：早期累计为负（回本前），跨过 0 后转正（净收益期），
    每根柱子高度真实反映累计盈亏，而非等高占位。
    """
    series: List[Dict] = []
    cumulative = -initial_investment
    for year, cf in enumerate(cashflows, start=1):
        cumulative += cf
        series.append(
            {
                "year": year,
                "net_cashflow_yuan": round(cf, 0),
                "cumulative_yuan": round(cumulative, 0),
            }
        )
    return series


def _npv_from_cashflows(initial_investment: float, cashflows: List[float], discount_rate: float) -> float:
    total = -initial_investment
    for year, cf in enumerate(cashflows, start=1):
        total += cf / ((1 + discount_rate) ** year)
    return round(total, 2)


def _annuity_factor(discount_rate: float, lifespan: int) -> float:
    if lifespan <= 0:
        return 0.0
    if discount_rate <= 0:
        return 1.0 / lifespan
    factor = (1 + discount_rate) ** lifespan
    return discount_rate * factor / (factor - 1)


def _eaa(npv_value: float, discount_rate: float, lifespan: int) -> float:
    """等额年值：把 NPV 摊到每年，跨寿命方案可公平比较（docs/28 §2.4）。"""
    return round(npv_value * _annuity_factor(discount_rate, lifespan), 2)


def _irr(initial_investment: float, cashflows: List[float]) -> Optional[float]:
    if initial_investment <= 0 or not cashflows or sum(cashflows) <= 0:
        return None
    lo, hi = 0.0, 2.0
    for _ in range(80):
        mid = (lo + hi) / 2
        npv_val = -initial_investment + sum(cf / ((1 + mid) ** year) for year, cf in enumerate(cashflows, start=1))
        if npv_val > 0:
            lo = mid
        else:
            hi = mid
    return round(min((lo + hi) / 2 * 100, 200.0), 1)


def _simple_payback_years(initial_investment: float, annual_saving_year1: float) -> float:
    if annual_saving_year1 <= 0:
        return 999.0
    return round(initial_investment / annual_saving_year1, 1)


def _discounted_payback_years(initial_investment: float, cashflows: List[float], discount_rate: float) -> float:
    cumulative = 0.0
    for year, cf in enumerate(cashflows, start=1):
        cumulative += cf / ((1 + discount_rate) ** year)
        if cumulative >= initial_investment:
            # 线性内插到小数年
            prev = cumulative - cf / ((1 + discount_rate) ** year)
            frac = (initial_investment - prev) / (cumulative - prev) if cumulative > prev else 0.0
            return round(year - 1 + frac, 1)
    return 999.0


def _payback_label(payback: float, lifespan: int) -> str:
    if payback >= 999 or payback > lifespan:
        return "寿命期内无法回本"
    return f"{payback} 年"


def build_equipment_audit(building_id: str) -> Dict:
    frame = _operational_frame()
    enriched = _get_enriched_frame(frame)
    # 只看该楼**实际出现过**的设备类型，不再遍历全数据集（docs/28 §3.1）。
    in_building = enriched[enriched["building_id"] == building_id]
    equipment_types = sorted(in_building["equipment_type"].dropna().unique().tolist())
    results = []

    for eq_type in equipment_types:
        stats = _building_equipment_stats(frame, building_id, eq_type)
        baseline = _EQUIPMENT_BASELINE.get(eq_type, {"typical_power_kw": 30, "typical_lifespan_years": 12})
        annual_kwh = stats["total_kwh"]
        annual_cost = round(annual_kwh * _ELECTRICITY_PRICE_YUAN_PER_KWH, 2)
        # COP=0（无制冷数据）不得判"低效"。
        if not stats["has_real_data"] or stats["avg_cop"] <= 0:
            cop_status = "无数据"
        elif stats["avg_cop"] < 2.4:
            cop_status = "低效"
        elif stats["avg_cop"] < 3.0:
            cop_status = "正常"
        else:
            cop_status = "高效"

        candidates = _retrofit_candidates(eq_type, stats) if stats["has_real_data"] else []

        results.append(
            {
                "equipment_type": eq_type,
                **stats,
                "annual_cost_yuan": annual_cost,
                "cop_status": cop_status,
                "typical_power_kw": baseline.get("typical_power_kw", 30),
                "typical_lifespan_years": baseline.get("typical_lifespan_years", 12),
                "data_note": "" if stats["has_real_data"] else "该楼无此设备实测数据，不产出改造方案。",
                "retrofit_candidates": candidates,
            }
        )

    building_name = (
        str(in_building["building_name"].iloc[0]) if not in_building.empty else building_id
    )
    return {
        "building_id": building_id,
        "building_name": building_name,
        "equipment_list": results,
        "data_scope": "simulation_visible",
        "generated_at": simulation_service.now_str(),
    }


def _retrofit_candidates(equipment_type: str, stats: Dict) -> List[Dict]:
    """仅在有实测数据时调用。基线电耗=实测年化；不再 max(实测, 铭牌)。"""
    baseline = _EQUIPMENT_BASELINE.get(equipment_type, {})
    invest_table = baseline.get("invest", {})
    target_cop = baseline.get("target_cop", 3.2)
    power_kw = baseline.get("typical_power_kw", 30)
    runtime_h = baseline.get("annual_runtime_h", 3000)
    annual_kwh = float(stats.get("total_kwh", 0))
    annual_cost = annual_kwh * _ELECTRICITY_PRICE_YUAN_PER_KWH
    gap_factor = _efficiency_gap_factor(float(stats.get("avg_cop", 0)), target_cop)

    # 等效设备台数 = 实测年电耗 ÷ 单台典型年电耗。投资按等效台数放大，强制让
    # "投资规模"与"被改造的电耗规模"匹配——避免小设备（如风机盘管单台 2.5kW）
    # 摊到整类大电耗时，单台投资极低而回收期≈0 的口径错配（docs/28 §2.1）。
    per_unit_annual_kwh = max(1.0, power_kw * runtime_h)
    effective_units = max(1, round(annual_kwh / per_unit_annual_kwh))

    candidates = []
    for option_name, option_params in _RETROFIT_OPTIONS.items():
        adj_saving_pct = min(0.60, option_params["base_saving_pct"] * gap_factor)
        lifespan = option_params["lifespan"]
        annual_saving = annual_cost * adj_saving_pct
        investment = float(invest_table.get(option_name, 0)) * effective_units
        cashflows = _cashflows(annual_saving, lifespan, _PRICE_ESCALATION)
        npv_val = _npv_from_cashflows(investment, cashflows, _DISCOUNT_RATE)
        payback = _simple_payback_years(investment, annual_saving)

        candidates.append(
            {
                "option": option_name,
                "investment_yuan": round(investment, 2),
                "annual_saving_yuan": round(annual_saving, 2),
                "saving_pct": round(adj_saving_pct * 100, 0),
                "lifespan_years": lifespan,
                "npv_yuan": npv_val,
                "irr_pct": _irr(investment, cashflows) or 0.0,
                "payback_years": payback,
                "eaa_yuan": _eaa(npv_val, _DISCOUNT_RATE, lifespan),
                "discounted_payback_years": _discounted_payback_years(investment, cashflows, _DISCOUNT_RATE),
                "saving_basis": _SAVING_BASIS,
                "investment_basis": option_params["investment_basis"],
            }
        )

    # 先按 NPV>0 可行，再按 EAA 最大（寿命不同，EAA 才公平）；不可行的排后面。
    return sorted(
        candidates,
        key=lambda c: (c["npv_yuan"] > 0, c["eaa_yuan"]),
        reverse=True,
    )


def _sensitivity_cases(investment: float, annual_saving: float, lifespan: int, expected_saving_pct: float) -> List[Dict]:
    """折现率敏感性：5% / 8% / 10% 三档（docs/28 §2.4）。"""
    results = []
    for rate in _SENSITIVITY_RATES:
        cashflows = _cashflows(annual_saving, lifespan, _PRICE_ESCALATION)
        npv_val = _npv_from_cashflows(investment, cashflows, rate)
        payback = _discounted_payback_years(investment, cashflows, rate)
        results.append(
            {
                "case": f"折现率 {rate * 100:.0f}%",
                "discount_rate": round(rate * 100, 0),
                "expected_saving_pct": round(expected_saving_pct * 100, 1),
                "annual_saving_yuan": round(annual_saving, 2),
                "npv_yuan": npv_val,
                "eaa_yuan": _eaa(npv_val, rate, lifespan),
                "payback_years": payback,
                "payback_label": _payback_label(payback, lifespan),
            }
        )
    return results


def analyze_roi_project(payload: Dict, include_sensitivity: bool = True) -> Dict:
    building_id = payload["building_id"]
    equipment_type = payload["equipment_type"]
    investment = float(payload["investment_yuan"])
    expected_saving_pct = float(payload.get("expected_saving_pct") or 0.20)
    annual_maintenance = float(payload.get("annual_maintenance_cost") or 0)
    discount_rate = float(payload.get("discount_rate") or _DISCOUNT_RATE)

    frame = _operational_frame()
    stats = _building_equipment_stats(frame, building_id, equipment_type)
    annual_kwh = stats["total_kwh"]
    annual_cost = annual_kwh * _ELECTRICITY_PRICE_YUAN_PER_KWH

    lifespan = int(payload.get("project_lifespan_years") or _LIFESPAN_MAP.get(equipment_type, 12))

    # 无实测数据：如实标注"数据不足"，不给推荐结论、不编造收益（docs/28 §5）。
    if not stats["has_real_data"] or annual_cost <= 0:
        return {
            "project_name": payload.get("project_name") or f"{equipment_type}节能改造项目",
            "building_id": building_id,
            "building_name": stats.get("building_name", building_id),
            "equipment_type": equipment_type,
            "investment_yuan": investment,
            "annual_saving_yuan": 0.0,
            "annual_saving_kwh": 0.0,
            "expected_saving_pct": round(expected_saving_pct * 100, 1),
            "project_lifespan_years": lifespan,
            "npv_yuan": 0.0,
            "irr_pct": 0.0,
            "eaa_yuan": 0.0,
            "payback_years": 999.0,
            "payback_label": "数据不足",
            "discounted_payback_years": 999.0,
            "payback_within_lifespan": False,
            "assessment": "数据不足",
            "has_real_data": False,
            "current_annual_kwh": round(annual_kwh, 2),
            "current_annual_cost_yuan": round(annual_cost, 2),
            "roi_5year_pct": 0.0,
            "carbon_reduction_kg_per_year": 0.0,
            "npv_with_carbon_yuan": 0.0,
            "discount_rate": round(discount_rate * 100, 0),
            "price_escalation": round(_PRICE_ESCALATION * 100, 0),
            "carbon_price_yuan_per_ton": _CARBON_PRICE_YUAN_PER_TON,
            "saving_basis": _SAVING_BASIS,
            "investment_basis": "—",
            "observed_days": stats.get("observed_days", 0),
            "annualization_factor": stats.get("annualization_factor", 0),
            "cumulative_cashflows": [],
            "data_scope": "simulation_visible",
            "generated_at": simulation_service.now_str(),
            "sensitivity": [] if include_sensitivity else None,
        }

    # 年净节省 = 年电费节省 − 增量运维；**不再有 0.15 兜底**，≤0 即如实"不经济"。
    annual_saving = annual_cost * expected_saving_pct - annual_maintenance
    annual_saving_kwh = max(0.0, annual_cost * expected_saving_pct) / _ELECTRICITY_PRICE_YUAN_PER_KWH

    cashflows = _cashflows(annual_saving, lifespan, _PRICE_ESCALATION)
    npv_val = _npv_from_cashflows(investment, cashflows, discount_rate)
    irr_val = _irr(investment, cashflows)
    eaa_val = _eaa(npv_val, discount_rate, lifespan)
    payback = _simple_payback_years(investment, annual_saving)
    discounted_payback = _discounted_payback_years(investment, cashflows, discount_rate)
    payback_within_lifespan = discounted_payback < 999 and discounted_payback <= lifespan

    # 含碳价情景（加分项，非主结论）。
    carbon_saving_kg = annual_saving_kwh * _CARBON_KG_PER_KWH
    carbon_value_year1 = carbon_saving_kg / 1000 * _CARBON_PRICE_YUAN_PER_TON
    cashflows_carbon = _cashflows(annual_saving + carbon_value_year1, lifespan, _PRICE_ESCALATION)
    npv_with_carbon = _npv_from_cashflows(investment, cashflows_carbon, discount_rate)

    if annual_saving <= 0 or npv_val < 0:
        assessment = "不推荐"
    elif not payback_within_lifespan:
        assessment = "不推荐"
    elif discounted_payback > 0.6 * lifespan:
        assessment = "谨慎推荐"
    elif discounted_payback > 0.35 * lifespan:
        assessment = "推荐"
    else:
        assessment = "强烈推荐"

    investment_basis = payload.get("investment_basis") or "改造直接投入 / 增量法"

    result = {
        "project_name": payload.get("project_name") or f"{equipment_type}节能改造项目",
        "building_id": building_id,
        "building_name": stats.get("building_name", building_id),
        "equipment_type": equipment_type,
        "investment_yuan": investment,
        "annual_saving_yuan": round(annual_saving, 2),
        "annual_saving_kwh": round(annual_saving_kwh, 2),
        "expected_saving_pct": round(expected_saving_pct * 100, 1),
        "project_lifespan_years": lifespan,
        "npv_yuan": npv_val,
        "irr_pct": irr_val if irr_val is not None else 0.0,
        "eaa_yuan": eaa_val,
        "payback_years": payback,
        "payback_label": _payback_label(discounted_payback, lifespan),
        "discounted_payback_years": discounted_payback,
        "payback_within_lifespan": payback_within_lifespan,
        "assessment": assessment,
        "has_real_data": True,
        "current_annual_kwh": round(annual_kwh, 2),
        "current_annual_cost_yuan": round(annual_cost, 2),
        "roi_5year_pct": round(_safe_divide(annual_saving * 5 - investment, investment) * 100, 1),
        "carbon_reduction_kg_per_year": round(carbon_saving_kg, 2),
        "npv_with_carbon_yuan": npv_with_carbon,
        "discount_rate": round(discount_rate * 100, 0),
        "price_escalation": round(_PRICE_ESCALATION * 100, 0),
        "carbon_price_yuan_per_ton": _CARBON_PRICE_YUAN_PER_TON,
        "saving_basis": _SAVING_BASIS,
        "investment_basis": investment_basis,
        "observed_days": stats.get("observed_days", 0),
        "annualization_factor": stats.get("annualization_factor", 0),
        "cumulative_cashflows": _cumulative_cashflow_series(investment, cashflows),
        "data_scope": "simulation_visible",
        "generated_at": simulation_service.now_str(),
    }
    if include_sensitivity:
        result["sensitivity"] = _sensitivity_cases(investment, annual_saving, lifespan, expected_saving_pct)
    return result


def compare_scenarios(payload: Dict) -> Dict:
    scenarios = payload.get("scenarios", [])
    if not scenarios:
        return {"scenarios": [], "comparison": {}, "recommendation": ""}

    results = [
        analyze_roi_project(s.model_dump() if hasattr(s, "model_dump") else s, include_sensitivity=False)
        for s in scenarios
    ]

    # 主判据：先筛 NPV>0，再按 EAA 最大（寿命不同，EAA 才公平）。
    feasible = [r for r in results if r["npv_yuan"] > 0 and r.get("payback_within_lifespan")]
    if feasible:
        best = max(feasible, key=lambda r: r["eaa_yuan"])
    else:
        best = max(results, key=lambda r: r["eaa_yuan"])
    fastest = min(feasible or results, key=lambda r: r["discounted_payback_years"])

    return {
        "scenarios": results,
        "comparison": {
            "best_npv": {"name": best["project_name"], "npv_yuan": best["npv_yuan"], "eaa_yuan": best["eaa_yuan"]},
            "best_eaa": {"name": best["project_name"], "eaa_yuan": best["eaa_yuan"]},
            "fastest_payback": {
                "name": fastest["project_name"],
                "payback_years": fastest["discounted_payback_years"],
                "payback_label": fastest["payback_label"],
            },
            "feasible_count": len(feasible),
            "scenario_count": len(results),
            "discount_rate": round(_DISCOUNT_RATE * 100, 0),
            "investment_range": {
                "min": round(min(r["investment_yuan"] for r in results), 2),
                "max": round(max(r["investment_yuan"] for r in results), 2),
            },
        },
        "recommendation": (
            f"按等额年值(EAA, 折现率 {_DISCOUNT_RATE * 100:.0f}%)，建议优先实施「{best['project_name']}」，"
            f"EAA={best['eaa_yuan']:,.0f} 元/年、NPV={best['npv_yuan']:,.0f} 元，"
            f"动态回收期 {best['payback_label']}。"
            if best["npv_yuan"] > 0
            else "各方案在 8% 折现率下 NPV 均不为正，按现状不具经济可行性，建议下调投资或提高能效差后重评。"
        ),
        "generated_at": simulation_service.now_str(),
    }
