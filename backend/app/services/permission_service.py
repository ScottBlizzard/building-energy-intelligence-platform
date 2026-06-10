"""Role helpers for the two-role demo workflow."""
from __future__ import annotations

from typing import Dict, List, Optional

from app.services.auth_service import get_user
from app.services.work_order_store import list_work_orders


class PermissionDenied(Exception):
    """Raised when a demo user tries to perform an action outside its role."""


def require_admin_operator(operator_id: Optional[str], action: str = "执行该操作") -> Dict:
    user = get_user(operator_id or "admin")
    if not user or user.get("role") != "admin":
        raise PermissionDenied(f"仅管理员可以{action}。")
    return user


def require_worker_operator(operator_id: Optional[str], action: str = "执行该操作") -> Dict:
    user = get_user(operator_id or "")
    if not user or user.get("role") != "worker":
        raise PermissionDenied(f"仅工人可以{action}。")
    return user


def standard_work_guidance(equipment_type: str = "", anomaly_reason: str = "") -> Dict:
    text = f"{equipment_type} {anomaly_reason}"
    if "冷水" in text or "CH" in text:
        steps = [
            "核对冷冻水供回水温差、流量和机组负载率。",
            "检查冷凝器换热、冷却水泵和冷却塔联动状态。",
            "处置后记录 COP、kWh 和控制信号恢复情况。",
        ]
        tools = ["红外测温仪", "钳形表", "楼控趋势截图"]
    elif "冷却" in text or "CT" in text:
        steps = [
            "检查风机、布水器和补水阀运行状态。",
            "清理填料和喷淋堵塞点，确认风机变频输出。",
            "复测冷却水温差并补充现场照片。",
        ]
        tools = ["测温枪", "风机电流表", "现场照片"]
    elif "风机" in text or "FCU" in text:
        steps = [
            "检查盘管滤网、风阀开度和末端温控器设定。",
            "确认凝结水排水和阀门动作正常。",
            "提交处理前后电耗或运行声音说明。",
        ]
        tools = ["滤网备件", "温湿度计", "末端控制面板截图"]
    else:
        steps = [
            "核对传感器读数和楼控趋势，确认是否为真实异常。",
            "检查风机、阀门、过滤器和控制策略是否偏离标准。",
            "处置后补充原因、处理动作、恢复确认和附件说明。",
        ]
        tools = ["楼控趋势截图", "巡检记录", "现场照片"]
    return {
        "title": "标准作业建议",
        "equipment_type": equipment_type or "通用设备",
        "anomaly_reason": anomaly_reason or "综合异常",
        "steps": steps,
        "required_evidence": tools,
    }


def similar_closed_cases(reference_order: Optional[Dict], limit: int = 3) -> List[Dict]:
    if not reference_order:
        return []
    ref_type = reference_order.get("equipment_type", "")
    ref_reason = reference_order.get("anomaly_reason", "")
    ref_id = reference_order.get("work_order_id", "")
    candidates = []
    for order in list_work_orders():
        if order.get("status") != "closed" or order.get("work_order_id") == ref_id:
            continue
        score = 0
        if order.get("equipment_type") == ref_type:
            score += 2
        if order.get("anomaly_reason") == ref_reason:
            score += 2
        if order.get("building_id") == reference_order.get("building_id"):
            score += 1
        if score <= 0:
            continue
        candidates.append(
            {
                "work_order_id": order.get("work_order_id"),
                "equipment_id": order.get("equipment_id"),
                "building_name": order.get("building_name"),
                "floor_label": order.get("floor_label"),
                "actual_cause": order.get("actual_cause") or "未填写",
                "resolution_note": order.get("resolution_note") or "未填写",
                "estimated_saving_yuan": order.get("estimated_saving_yuan") or 0,
                "closed_at": order.get("closed_at") or order.get("updated_at"),
                "match_score": score,
            }
        )
    return sorted(candidates, key=lambda item: (item["match_score"], item.get("closed_at") or ""), reverse=True)[:limit]


def build_worker_support(user_id: str) -> Dict:
    orders = list_work_orders(assignee_id=user_id, role="worker")
    active = [
        item for item in orders
        if item.get("status") in {"assigned", "in_progress", "rejected", "pending_review"}
    ]
    reference = active[0] if active else (orders[0] if orders else None)
    return {
        "standard_work_guidance": standard_work_guidance(
            reference.get("equipment_type", "") if reference else "",
            reference.get("anomaly_reason", "") if reference else "",
        ),
        "similar_cases": similar_closed_cases(reference),
    }
