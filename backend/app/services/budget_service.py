from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from app.core.config import get_settings
from app.services.analysis_service import _add_operational_dimensions, _safe_divide
from app.services.data_loader import get_visible_dataset
from app.services.work_order_store import list_work_orders

_SEASONAL_COEFFICIENTS = {1: 1.15, 2: 1.10, 3: 0.95, 4: 0.85, 5: 0.80, 6: 0.90, 7: 1.10, 8: 1.15, 9: 0.95, 10: 0.80, 11: 0.90, 12: 1.10}


def _budget_path() -> Path:
    configured_path = os.getenv("BUDGET_FILE")
    if configured_path:
        path = Path(configured_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    settings = get_settings()
    path = settings.root_dir / "data" / "runtime" / "budgets.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _read_budgets() -> List[Dict]:
    path = _budget_path()
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return payload if isinstance(payload, list) else []


def _write_budgets(items: List[Dict]) -> None:
    path = _budget_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def _operational_frame():
    """Dataset view used by business decisions.

    During a simulation run this hides unrevealed future records and applies
    approved repair interventions. When simulation is inactive it is equivalent
    to the full sample dataset.
    """
    return get_visible_dataset()


def _monthly_projection(subset) -> float:
    if subset.empty:
        return 0.0
    observed_days = max(1, int(subset["timestamp"].dt.normalize().nunique()))
    return float(subset["electricity_kwh"].sum() / observed_days * 30)


def _building_budget_baseline(frame, building_id: str, month: int) -> tuple[float, str]:
    same_month = frame[(frame["building_id"] == building_id) & (frame["timestamp"].dt.month == month)]
    if not same_month.empty:
        return _monthly_projection(same_month), "同月历史均值"

    building_rows = frame[frame["building_id"] == building_id]
    if not building_rows.empty:
        return _monthly_projection(building_rows), "楼栋可见数据均值"

    if not frame.empty:
        return _monthly_projection(frame), "全局样本均值"

    return 80000.0, "默认兜底基线"


def auto_generate_budgets(year: int, month: int) -> List[Dict]:
    frame = _operational_frame()
    buildings = frame["building_id"].unique()
    existing = _read_budgets()
    existing_keys = {(item["building_id"], item["year"], item["month"]) for item in existing}
    new_items = []

    for building_id in sorted(buildings):
        key = (str(building_id), year, month)
        if key in existing_keys:
            continue
        baseline, basis = _building_budget_baseline(frame, str(building_id), month)
        coefficient = _SEASONAL_COEFFICIENTS.get(month, 1.0)
        budget = round(baseline * coefficient * 0.92, 0)
        item = {
            "building_id": str(building_id),
            "building_name": str(frame[frame["building_id"] == building_id]["building_name"].iloc[0]),
            "year": year,
            "month": month,
            "budget_kwh": budget if budget > 0 else 80000.0,
            "note": f"基于{basis}自动生成，季节系数 {coefficient}",
            "basis": basis,
            "seasonal_coefficient": coefficient,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        new_items.append(item)

    _write_budgets(existing + new_items)
    return _read_budgets()


def list_budgets(year: Optional[int] = None, month: Optional[int] = None) -> List[Dict]:
    items = _read_budgets()
    if year:
        items = [item for item in items if item["year"] == year]
    if month:
        items = [item for item in items if item["month"] == month]
    return sorted(items, key=lambda item: (item.get("year", 0), item.get("month", 0), item.get("building_name", "")))


def set_budget(payload: Dict) -> Dict:
    items = _read_budgets()
    existing = next(
        (
            item
            for item in items
            if item["building_id"] == payload["building_id"]
            and item["year"] == payload["year"]
            and item["month"] == payload["month"]
        ),
        None,
    )
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if existing:
        existing["budget_kwh"] = payload["budget_kwh"]
        existing["note"] = payload.get("note", existing.get("note", ""))
        existing["updated_at"] = now
    else:
        frame = _operational_frame()
        building_rows = frame[frame["building_id"] == payload["building_id"]]
        building_name = str(building_rows["building_name"].iloc[0]) if not building_rows.empty else payload["building_id"]
        items.append(
            {
                "building_id": payload["building_id"],
                "building_name": building_name,
                "year": payload["year"],
                "month": payload["month"],
                "budget_kwh": payload["budget_kwh"],
                "note": payload.get("note", ""),
                "created_at": now,
                "updated_at": now,
            }
        )
    _write_budgets(items)
    return build_budget_analysis(payload["year"], payload["month"])


def build_budget_analysis(year: int, month: int) -> Dict:
    frame = _add_operational_dimensions(_operational_frame())
    budgets = {item["building_id"]: item for item in _read_budgets() if item["year"] == year and item["month"] == month}

    if not budgets:
        auto_generate_budgets(year, month)
        budgets = {item["building_id"]: item for item in _read_budgets() if item["year"] == year and item["month"] == month}

    month_frame = frame[frame["timestamp"].dt.month == month]
    building_details = []
    total_actual = 0.0
    total_budget = 0.0
    total_month_end_estimate = 0.0

    for building_id, budget_item in sorted(budgets.items()):
        building_data = month_frame[month_frame["building_id"] == building_id]
        actual_kwh = round(float(building_data["electricity_kwh"].sum()), 2) if not building_data.empty else 0.0
        budget_kwh = float(budget_item["budget_kwh"])
        execution_rate = round(_safe_divide(actual_kwh, budget_kwh) * 100, 1)
        variance = round(actual_kwh - budget_kwh, 2)
        anomaly_count = int(building_data["is_anomaly"].sum()) if not building_data.empty and "is_anomaly" in building_data.columns else 0
        observed_days = int(building_data["timestamp"].dt.normalize().nunique()) if not building_data.empty else 0
        month_end_estimate = round(_safe_divide(actual_kwh, max(observed_days, 1)) * 30, 2) if observed_days else 0.0
        projected_execution_rate = round(_safe_divide(month_end_estimate, budget_kwh) * 100, 1)

        total_actual += actual_kwh
        total_budget += budget_kwh
        total_month_end_estimate += month_end_estimate

        status = "healthy"
        if projected_execution_rate > 100:
            status = "over"
        elif projected_execution_rate > 85:
            status = "warning"

        building_details.append(
            {
                "building_id": building_id,
                "building_name": budget_item.get("building_name", building_id),
                "budget_kwh": budget_kwh,
                "actual_kwh": actual_kwh,
                "execution_rate": execution_rate,
                "observed_days": observed_days,
                "month_end_estimate_kwh": month_end_estimate,
                "projected_execution_rate": projected_execution_rate,
                "variance_kwh": variance,
                "anomaly_count": anomaly_count,
                "status": status,
                "note": budget_item.get("note", ""),
            }
        )

    total_execution_rate = round(_safe_divide(total_actual, total_budget) * 100, 1) if total_budget > 0 else 0.0
    total_projected_execution_rate = (
        round(_safe_divide(total_month_end_estimate, total_budget) * 100, 1)
        if total_budget > 0
        else 0.0
    )

    return {
        "year": year,
        "month": month,
        "total_budget_kwh": round(total_budget, 2),
        "total_actual_kwh": round(total_actual, 2),
        "total_month_end_estimate_kwh": round(total_month_end_estimate, 2),
        "total_execution_rate": total_execution_rate,
        "total_projected_execution_rate": total_projected_execution_rate,
        "buildings": building_details,
        "over_budget_count": sum(1 for b in building_details if b["status"] == "over"),
        "warning_count": sum(1 for b in building_details if b["status"] == "warning"),
        "healthy_count": sum(1 for b in building_details if b["status"] == "healthy"),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def build_budget_kpi(building_id: str, year: int) -> Dict:
    frame = _add_operational_dimensions(_operational_frame())
    budgets = _read_budgets()
    building_budgets = [b for b in budgets if b["building_id"] == building_id and b["year"] == year]

    monthly_scores = []
    total_budget = 0.0
    total_actual = 0.0
    for budget_item in building_budgets:
        month = budget_item["month"]
        month_frame = frame[(frame["building_id"] == building_id) & (frame["timestamp"].dt.month == month)]
        actual = float(month_frame["electricity_kwh"].sum()) if not month_frame.empty else 0.0
        budget_kwh = float(budget_item["budget_kwh"])
        exec_rate = _safe_divide(actual, budget_kwh)
        observed_days = int(month_frame["timestamp"].dt.normalize().nunique()) if not month_frame.empty else 0
        projected_exec_rate = _safe_divide(_safe_divide(actual, max(observed_days, 1)) * 30, budget_kwh) if observed_days else exec_rate
        cop_pass_rate = (
            _safe_divide(int((month_frame["average_cop"] >= 2.4).sum()), len(month_frame)) * 100
            if not month_frame.empty and "average_cop" in month_frame.columns
            else 0.0
        )
        total_budget += budget_kwh
        total_actual += actual

        score = 100.0
        if projected_exec_rate > 1.0:
            score -= min(30, (projected_exec_rate - 1.0) * 100)
        if projected_exec_rate < 0.5:
            score -= 5

        anomaly_count = int(month_frame["is_anomaly"].sum()) if not month_frame.empty and "is_anomaly" in month_frame.columns else 0
        response_metrics = _work_order_response_metrics(building_id, year, month)
        anomaly_response_rate = (
            response_metrics["timely_rate"]
            if response_metrics
            else max(0.0, 100.0 - max(0, anomaly_count - 10) * 5)
        )
        if anomaly_count > 10:
            score -= min(15, anomaly_count * 0.5)
        if cop_pass_rate < 80:
            score -= min(15, (80 - cop_pass_rate) * 0.25)
        if anomaly_response_rate < 80:
            score -= min(10, (80 - anomaly_response_rate) * 0.2)

        monthly_scores.append(
            {
                "month": month,
                "budget_kwh": budget_kwh,
                "actual_kwh": round(actual, 2),
                "execution_rate": round(exec_rate * 100, 1),
                "projected_execution_rate": round(projected_exec_rate * 100, 1),
                "cop_pass_rate": round(cop_pass_rate, 1),
                "anomaly_count": anomaly_count,
                "anomaly_response_timely_rate": round(anomaly_response_rate, 1),
                "response_order_count": response_metrics["total"] if response_metrics else 0,
                "response_timely_count": response_metrics["timely"] if response_metrics else 0,
                "score": round(max(0, score), 1),
            }
        )

    overall_exec_rate = _safe_divide(total_actual, total_budget) * 100
    avg_score = round(sum(m["score"] for m in monthly_scores) / len(monthly_scores), 1) if monthly_scores else 0

    grade = "A"
    if avg_score < 60:
        grade = "D"
    elif avg_score < 75:
        grade = "C"
    elif avg_score < 85:
        grade = "B"

    building_name = str(frame[frame["building_id"] == building_id]["building_name"].iloc[0]) if not frame.empty else building_id

    return {
        "building_id": building_id,
        "building_name": building_name,
        "year": year,
        "overall_execution_rate": round(overall_exec_rate, 1),
        "total_actual_kwh": round(total_actual, 2),
        "total_budget_kwh": round(total_budget, 2),
        "average_score": avg_score,
        "grade": grade,
        "budget_control_rate": round(100 - max(0, overall_exec_rate - 100), 1),
        "cop_pass_rate": round(
            sum(m["cop_pass_rate"] for m in monthly_scores) / len(monthly_scores),
            1,
        )
        if monthly_scores
        else 0,
        "anomaly_response_timely_rate": round(
            sum(m["anomaly_response_timely_rate"] for m in monthly_scores) / len(monthly_scores),
            1,
        )
        if monthly_scores
        else 0,
        "monthly_details": monthly_scores,
        "strengths": _identify_strengths(monthly_scores),
        "improvements": _identify_improvements(monthly_scores),
    }


def _identify_strengths(scores: List[Dict]) -> List[str]:
    strengths = []
    under_budget = [m for m in scores if m["projected_execution_rate"] < 95]
    if under_budget:
        months = "、".join(f"{m['month']}月" for m in under_budget[:3])
        strengths.append(f"{months} 用电控制在预算以内，执行率良好。")
    if scores and all(m["anomaly_count"] < 5 for m in scores):
        strengths.append("全年异常事件较少，设备运行状态整体稳定。")
    if scores and all(m["anomaly_response_timely_rate"] >= 90 for m in scores):
        strengths.append("异常工单响应及时率较高，运维闭环执行稳定。")
    return strengths or ["月度能耗管理基本达标。"]


def _identify_improvements(scores: List[Dict]) -> List[str]:
    improvements = []
    over_budget = [m for m in scores if m["projected_execution_rate"] > 100]
    if over_budget:
        months = "、".join(f"{m['month']}月" for m in over_budget[:3])
        improvements.append(f"{months} 超出预算，建议分析用电高峰原因并制定节能策略。")
    high_anomaly = [m for m in scores if m["anomaly_count"] > 10]
    if high_anomaly:
        improvements.append("异常事件较多月份建议加强巡检和设备维护。")
    slow_response = [m for m in scores if m["anomaly_response_timely_rate"] < 80]
    if slow_response:
        months = "、".join(f"{m['month']}月" for m in slow_response[:3])
        improvements.append(f"{months} 工单响应及时率偏低，建议明确派单 SLA 和复核责任人。")
    return improvements or ["建议持续跟踪预算执行情况，优化设备运行策略。"]


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _work_order_response_metrics(building_id: str, year: int, month: int) -> Optional[Dict]:
    orders = []
    for order in list_work_orders():
        if order.get("building_id") != building_id:
            continue
        order_time = _parse_datetime(order.get("timestamp")) or _parse_datetime(order.get("created_at"))
        if not order_time or order_time.year != year or order_time.month != month:
            continue
        orders.append(order)

    if not orders:
        return None

    timely = 0
    for order in orders:
        opened_at = _parse_datetime(order.get("created_at")) or _parse_datetime(order.get("timestamp"))
        response_at = _first_response_time(order)
        if not opened_at or not response_at:
            continue
        priority = str(order.get("priority", "中"))
        sla_hours = 8 if priority == "高" else 24 if priority == "中" else 72
        elapsed_hours = (response_at - opened_at).total_seconds() / 3600
        if elapsed_hours <= sla_hours:
            timely += 1

    return {
        "total": len(orders),
        "timely": timely,
        "timely_rate": round(_safe_divide(timely, len(orders)) * 100, 1),
    }


def _first_response_time(order: Dict) -> Optional[datetime]:
    response_statuses = {"assigned", "in_progress", "pending_review", "closed", "ignored"}
    response_actions = {"assign", "accept", "submit", "review_approve", "ignore"}
    candidates = []
    for event in order.get("timeline", []) or []:
        if event.get("action") in response_actions or event.get("to_status") in response_statuses:
            event_time = _parse_datetime(event.get("created_at"))
            if event_time:
                candidates.append(event_time)
    closed_at = _parse_datetime(order.get("closed_at"))
    if closed_at:
        candidates.append(closed_at)
    return min(candidates) if candidates else None
