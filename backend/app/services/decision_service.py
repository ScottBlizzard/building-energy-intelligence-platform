"""Economic decision helpers for the operational loop.

The decision layer turns anomaly work orders into management actions: which
orders to dispatch first, how much closed orders improve the budget forecast,
and which repeatedly failing equipment should enter an ROI retrofit pool.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional

from app.services import simulation_service
from app.services.auth_service import resolve_worker_for_equipment
from app.services.budget_service import build_budget_analysis
from app.services.data_loader import get_visible_dataset
from app.services.work_order_store import list_work_orders

_PRICE_YUAN_PER_KWH = 0.82
_CARBON_KG_PER_KWH = 0.5703
_OPEN_STATUSES = {"pending_confirm", "assigned", "in_progress", "pending_review", "rejected"}
_PRIORITY_RISK_FALLBACK = {"高": 78.0, "中": 55.0, "低": 32.0}
_PRIORITY_LOSS_FALLBACK = {"高": 180.0, "中": 80.0, "低": 30.0}


def _as_float(value, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _open_orders() -> List[Dict]:
    return [item for item in list_work_orders() if item.get("status") in _OPEN_STATUSES]


def _anomaly_candidate_orders(limit: int = 12) -> List[Dict]:
    """Fallback dispatch candidates derived from the currently visible anomalies.

    When no work order has been created yet (e.g. right after starting the time
    machine in a demo), the priority panel would otherwise be empty. We surface
    the live anomalies as candidate "orders" so the panel is immediately useful;
    each item is flagged so the UI can label it as "not yet ticketed".
    """
    try:
        from app.services.analysis_service import build_analysis_frame, build_anomaly_work_orders

        candidates = build_anomaly_work_orders(build_analysis_frame(get_visible_dataset()))
    except (FileNotFoundError, ValueError, KeyError):
        return []
    out = []
    for candidate in candidates[: max(1, int(limit))]:
        item = dict(candidate)
        item["status"] = item.get("status") or "pending_confirm"
        item["from_anomaly_candidate"] = True
        out.append(item)
    return out


def _live_impact_by_record() -> Dict[str, Dict]:
    """Map source_record_id -> live business-impact fields for currently visible
    anomalies. Used so a dispatch card's score reason matches exactly what the
    work-order preview strip shows for the same record (no preview/hint drift)."""
    try:
        from app.services.analysis_service import build_analysis_frame, build_anomaly_summary

        records = build_anomaly_summary(build_analysis_frame(get_visible_dataset()))
    except (FileNotFoundError, ValueError, KeyError):
        return {}
    impact_fields = (
        "risk_score",
        "wasted_cost_yuan",
        "estimated_saving_yuan",
        "carbon_kg",
        "wasted_kwh",
        "sla_hours",
    )
    out: Dict[str, Dict] = {}
    for record in records:
        record_id = str(record.get("record_id") or "")
        if not record_id:
            continue
        out[record_id] = {field: record[field] for field in impact_fields if field in record}
    return out


def _equipment_repeat_counts(orders: List[Dict]) -> Dict[str, int]:
    counts: Dict[str, int] = defaultdict(int)
    for order in orders:
        equipment_id = str(order.get("equipment_id") or "")
        if equipment_id:
            counts[equipment_id] += 1
    return counts


def _normalize(value: float, max_value: float) -> float:
    if max_value <= 0:
        return 0.0
    return max(0.0, min(1.0, value / max_value))


def _risk_estimate(order: Dict) -> tuple[float, bool]:
    risk = _as_float(order.get("risk_score"))
    if risk > 0:
        return risk, False
    return _PRIORITY_RISK_FALLBACK.get(str(order.get("priority") or "中"), 45.0), True


def _loss_estimate(order: Dict) -> tuple[float, bool]:
    cost = _as_float(order.get("wasted_cost_yuan"))
    if cost > 0:
        return cost, False

    saving = _as_float(order.get("estimated_saving_yuan"))
    if saving > 0:
        return round(saving / 0.75, 2), False

    before_kwh = _as_float(order.get("before_kwh"))
    after_kwh = _as_float(order.get("after_kwh"), before_kwh)
    if before_kwh > after_kwh:
        return round((before_kwh - after_kwh) * _PRICE_YUAN_PER_KWH, 2), False

    risk, _ = _risk_estimate(order)
    priority = str(order.get("priority") or "中")
    return max(_PRIORITY_LOSS_FALLBACK.get(priority, 60.0), risk * 1.35), True


def _carbon_estimate(order: Dict, loss_yuan: float) -> tuple[float, bool]:
    carbon = _as_float(order.get("carbon_kg"))
    if carbon > 0:
        return carbon, False
    wasted_kwh = _as_float(order.get("wasted_kwh"))
    if wasted_kwh > 0:
        return round(wasted_kwh * _CARBON_KG_PER_KWH, 2), False
    if loss_yuan > 0:
        return round((loss_yuan / _PRICE_YUAN_PER_KWH) * _CARBON_KG_PER_KWH, 2), True
    return 0.0, False


def _saving_estimate(order: Dict, loss_yuan: float) -> tuple[float, bool]:
    saving = _as_float(order.get("estimated_saving_yuan"))
    if saving > 0:
        return saving, False
    return round(loss_yuan * 0.75, 2), True


def rank_open_work_orders(limit: int = 10) -> List[Dict]:
    # Always combine the real open work orders with the remaining live anomaly
    # candidates that have not been ticketed yet. This keeps the dispatch panel
    # showing the full prioritized worklist: dispatching one order no longer
    # collapses the panel down to that single order.
    open_orders = _open_orders()
    open_equipment = {str(item.get("equipment_id") or "") for item in open_orders}
    candidates = [
        candidate
        for candidate in _anomaly_candidate_orders(limit=max(20, int(limit) * 3))
        if str(candidate.get("equipment_id") or "") not in open_equipment
    ]
    orders = list(open_orders) + candidates
    if not orders:
        return []

    # Refresh each order with the live impact of its source anomaly record (when
    # still visible) so the dispatch reason equals the preview strip values.
    live_impact = _live_impact_by_record()
    if live_impact:
        enriched_orders = []
        for order in orders:
            record_id = str(order.get("source_record_id") or "")
            if record_id and record_id in live_impact:
                order = {**order, **live_impact[record_id]}
            enriched_orders.append(order)
        orders = enriched_orders

    repeat_counts = _equipment_repeat_counts(list_work_orders() + candidates)
    loss_pairs = [_loss_estimate(item) for item in orders]
    carbon_pairs = [_carbon_estimate(item, loss) for item, (loss, _) in zip(orders, loss_pairs)]
    max_loss = max(loss for loss, _ in loss_pairs) or 1.0
    max_carbon = max(carbon for carbon, _ in carbon_pairs) or 1.0

    ranked = []
    for order, (loss, loss_estimated), (carbon, carbon_estimated) in zip(orders, loss_pairs, carbon_pairs):
        risk, risk_estimated = _risk_estimate(order)
        saving, saving_estimated = _saving_estimate(order, loss)
        sla_hours = max(1, _as_int(order.get("sla_hours"), 24))
        equipment_id = str(order.get("equipment_id") or "")
        repeat_count = repeat_counts.get(equipment_id, 1)
        is_candidate = bool(order.get("from_anomaly_candidate"))

        risk_component = _normalize(risk, 100) * 40
        loss_component = _normalize(loss, max_loss) * 25
        sla_component = _normalize(max(0, 72 - sla_hours), 72) * 15
        carbon_component = _normalize(carbon, max_carbon) * 10
        repeat_component = min(10.0, max(0, repeat_count - 1) * 4.0)
        score = round(
            risk_component + loss_component + sla_component + carbon_component + repeat_component,
            1,
        )
        worker = resolve_worker_for_equipment(equipment_id, str(order.get("equipment_type") or ""))
        ranked.append(
            {
                "work_order_id": order.get("work_order_id"),
                "source_record_id": order.get("source_record_id"),
                "equipment_id": equipment_id,
                "equipment_type": order.get("equipment_type", ""),
                "building_id": order.get("building_id", ""),
                "building_name": order.get("building_name", ""),
                "floor_label": order.get("floor_label", ""),
                "status": order.get("status", ""),
                "status_label": order.get("status_label", ""),
                "priority": order.get("priority", ""),
                "is_candidate": is_candidate,
                "decision_score": score,
                "score_breakdown": {
                    "risk": round(risk_component, 1),
                    "estimated_loss": round(loss_component, 1),
                    "sla": round(sla_component, 1),
                    "carbon": round(carbon_component, 1),
                    "repeat_anomaly": round(repeat_component, 1),
                },
                "risk_score": risk,
                "wasted_cost_yuan": round(loss, 2),
                "estimated_saving_yuan": round(saving, 2),
                "carbon_kg": round(carbon, 2),
                "sla_hours": sla_hours,
                "repeat_count": repeat_count,
                "estimate_flags": {
                    "risk": risk_estimated,
                    "loss": loss_estimated,
                    "saving": saving_estimated,
                    "carbon": carbon_estimated,
                },
                "recommended_worker_id": order.get("assignee_id") or worker["user_id"],
                "recommended_worker_name": order.get("assignee_name") or worker["display_name"],
                "reason": (
                    f"风险 {risk:.1f} 分，预计损失 {loss:.0f} 元，SLA {sla_hours} 小时，"
                    f"碳排影响 {carbon:.1f} kg，历史同设备异常 {repeat_count} 次。"
                ),
            }
        )

    return sorted(ranked, key=lambda item: item["decision_score"], reverse=True)[: max(1, int(limit))]


def recommend_dispatch_plan(worker_capacity: int = 3) -> Dict:
    capacity = max(1, int(worker_capacity or 3))
    ranked = rank_open_work_orders(limit=max(capacity, 10))
    selected = ranked[:capacity]
    deferred = ranked[capacity:]
    total_loss = round(sum(_as_float(item.get("wasted_cost_yuan")) for item in selected), 2)
    total_saving = round(sum(_as_float(item.get("estimated_saving_yuan")) for item in selected), 2)
    total_carbon = round(sum(_as_float(item.get("carbon_kg")) for item in selected), 2)
    return {
        "worker_capacity": capacity,
        "selected": selected,
        "deferred": deferred[:5],
        "total_selected_loss_yuan": total_loss,
        "total_selected_recoverable_yuan": total_saving,
        "total_selected_carbon_kg": total_carbon,
        "summary": (
            f"今天若只能派 {capacity} 名工人，建议优先处理 {len(selected)} 个高分工单，"
            f"覆盖约 {total_loss:,.0f} 元预计损失、{total_carbon:,.1f} kg 碳排影响。"
            if selected
            else "当前没有待处理工单，可把人力用于巡检和复盘。"
        ),
        "generated_at": simulation_service.now_str(),
    }


def summarize_budget_impact_from_closures(year: Optional[int] = None, month: Optional[int] = None) -> Dict:
    closed = [item for item in list_work_orders() if item.get("status") == "closed"]
    building_impacts: Dict[str, Dict] = {}

    for order in closed:
        building_id = str(order.get("building_id") or "")
        if not building_id:
            continue
        impact = building_impacts.setdefault(
            building_id,
            {
                "building_id": building_id,
                "building_name": order.get("building_name", building_id),
                "closed_order_count": 0,
                "saved_kwh": 0.0,
                "recoverable_yuan": 0.0,
                "carbon_kg": 0.0,
            },
        )
        before_kwh = _as_float(order.get("before_kwh"))
        after_kwh = _as_float(order.get("after_kwh"), before_kwh)
        saved_kwh = max(0.0, before_kwh - after_kwh)
        if saved_kwh <= 0:
            saved_kwh = _as_float(order.get("estimated_saving_yuan")) / _PRICE_YUAN_PER_KWH
        impact["closed_order_count"] += 1
        impact["saved_kwh"] += saved_kwh
        impact["recoverable_yuan"] += _as_float(order.get("estimated_saving_yuan"), saved_kwh * _PRICE_YUAN_PER_KWH)
        impact["carbon_kg"] += saved_kwh * _CARBON_KG_PER_KWH

    buildings = []
    for item in building_impacts.values():
        item["saved_kwh"] = round(item["saved_kwh"], 2)
        item["recoverable_yuan"] = round(item["recoverable_yuan"], 2)
        item["carbon_kg"] = round(item["carbon_kg"], 2)
        buildings.append(item)

    total_saved_kwh = round(sum(item["saved_kwh"] for item in buildings), 2)
    total_saving_yuan = round(sum(item["recoverable_yuan"] for item in buildings), 2)
    total_carbon_kg = round(sum(item["carbon_kg"] for item in buildings), 2)

    budget_projection = None
    if year and month:
        analysis = build_budget_analysis(int(year), int(month))
        adjusted_estimate = max(0.0, _as_float(analysis.get("total_month_end_estimate_kwh")) - total_saved_kwh)
        total_budget = _as_float(analysis.get("total_budget_kwh"))
        budget_projection = {
            "before_month_end_estimate_kwh": analysis.get("total_month_end_estimate_kwh", 0),
            "after_closure_month_end_estimate_kwh": round(adjusted_estimate, 2),
            "before_projected_execution_rate": analysis.get("total_projected_execution_rate", 0),
            "after_projected_execution_rate": round((adjusted_estimate / total_budget * 100) if total_budget else 0, 1),
        }

    return {
        "closed_order_count": len(closed),
        "total_saved_kwh": total_saved_kwh,
        "total_saving_yuan": total_saving_yuan,
        "total_carbon_kg": total_carbon_kg,
        "buildings": sorted(buildings, key=lambda item: item["recoverable_yuan"], reverse=True),
        "budget_projection": budget_projection,
        "summary": (
            f"已关闭工单使预算预测减少约 {total_saved_kwh:,.1f} kWh，"
            f"折合 {total_saving_yuan:,.0f} 元、{total_carbon_kg:,.1f} kg 碳排。"
            if closed
            else "暂无已关闭工单，预算预测尚未获得处置收益修正。"
        ),
        "generated_at": simulation_service.now_str(),
    }


def _visible_anomaly_counts() -> Dict[str, Dict]:
    try:
        from app.services.analysis_service import _add_operational_dimensions

        frame = _add_operational_dimensions(get_visible_dataset())
    except (FileNotFoundError, ValueError, KeyError):
        return {}
    if frame.empty or "is_anomaly" not in frame.columns:
        return {}
    anomalies = frame[frame["is_anomaly"]].copy()
    result: Dict[str, Dict] = {}
    for equipment_id, group in anomalies.groupby("equipment_id"):
        result[str(equipment_id)] = {
            "visible_anomaly_count": int(len(group)),
            "building_id": str(group["building_id"].iloc[0]),
            "building_name": str(group["building_name"].iloc[0]),
            "equipment_type": str(group["equipment_type"].iloc[0]),
        }
    return result


def _roi_candidate_reason(item: Dict, repeat_count: int) -> str:
    open_count = int(item.get("open_count", 0))
    visible = int(item.get("visible_anomaly_count", 0))
    cumulative_loss = float(item.get("cumulative_loss_yuan", 0) or 0)
    parts = [f"累计异常/工单 {repeat_count} 次"]
    if cumulative_loss > 0:
        parts.append(f"已建单累计损失约 {cumulative_loss:,.0f} 元")
    elif visible > 0:
        parts.append(f"当前可见异常 {visible} 条（尚未建单，损失按实时估算）")
    if open_count > 0:
        parts.append(f"仍有 {open_count} 个未闭环工单")
    return "，".join(parts) + "。"


def find_roi_candidates_from_repeated_anomalies(limit: int = 8) -> List[Dict]:
    orders = list_work_orders()
    grouped: Dict[str, Dict] = {}
    visible_counts = _visible_anomaly_counts()

    for order in orders:
        equipment_id = str(order.get("equipment_id") or "")
        if not equipment_id:
            continue
        item = grouped.setdefault(
            equipment_id,
            {
                "equipment_id": equipment_id,
                "equipment_type": order.get("equipment_type", ""),
                "building_id": order.get("building_id", ""),
                "building_name": order.get("building_name", ""),
                "order_count": 0,
                "closed_count": 0,
                "open_count": 0,
                "cumulative_loss_yuan": 0.0,
                "cumulative_saving_yuan": 0.0,
                "carbon_kg": 0.0,
            },
        )
        item["order_count"] += 1
        if order.get("status") == "closed":
            item["closed_count"] += 1
        elif order.get("status") not in {"ignored"}:
            item["open_count"] += 1
        item["cumulative_loss_yuan"] += _as_float(order.get("wasted_cost_yuan"))
        item["cumulative_saving_yuan"] += _as_float(order.get("estimated_saving_yuan"))
        item["carbon_kg"] += _as_float(order.get("carbon_kg"))

    for equipment_id, visible in visible_counts.items():
        item = grouped.setdefault(
            equipment_id,
            {
                "equipment_id": equipment_id,
                "equipment_type": visible.get("equipment_type", ""),
                "building_id": visible.get("building_id", ""),
                "building_name": visible.get("building_name", ""),
                "order_count": 0,
                "closed_count": 0,
                "open_count": 0,
                "cumulative_loss_yuan": 0.0,
                "cumulative_saving_yuan": 0.0,
                "carbon_kg": 0.0,
            },
        )
        item["visible_anomaly_count"] = visible.get("visible_anomaly_count", 0)

    candidates = []
    for item in grouped.values():
        repeat_count = int(item.get("order_count", 0)) + int(item.get("visible_anomaly_count", 0))
        if repeat_count < 2 and item["cumulative_loss_yuan"] <= 0:
            continue
        retrofit_score = round(
            min(100.0, repeat_count * 14 + item["cumulative_loss_yuan"] * 0.05 + item["open_count"] * 6),
            1,
        )
        option = "智能控制升级"
        if "冷水" in item.get("equipment_type", ""):
            option = "高效冷水机组或变频改造"
        elif "冷却" in item.get("equipment_type", ""):
            option = "冷却塔变频与布水优化"
        elif "空气" in item.get("equipment_type", ""):
            option = "AHU 风机变频与传感器校准"
        candidates.append(
            {
                **item,
                "repeat_count": repeat_count,
                "retrofit_score": retrofit_score,
                "recommended_option": option,
                "budget_effect": "通过后写入下一轮预算基线，降低未来异常概率假设。",
                "reason": _roi_candidate_reason(item, repeat_count),
            }
        )

    for item in candidates:
        item["cumulative_loss_yuan"] = round(item["cumulative_loss_yuan"], 2)
        item["cumulative_saving_yuan"] = round(item["cumulative_saving_yuan"], 2)
        item["carbon_kg"] = round(item["carbon_kg"], 2)

    return sorted(candidates, key=lambda item: item["retrofit_score"], reverse=True)[: max(1, int(limit))]
