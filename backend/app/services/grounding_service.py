"""Ground assistant answers in current business data.

This module keeps the external LLM useful without letting it invent work-order
or equipment facts. It builds a compact real-time context from the runtime work
order store, validates model output against known entity ids, and provides a
deterministic fallback answer when validation fails.
"""
from __future__ import annotations

import re
from typing import Dict, List

from app.services.work_order_store import list_work_orders


WORK_ORDER_RE = re.compile(r"\bWO-[A-Z0-9-]+\b", re.IGNORECASE)
EQUIPMENT_RE = re.compile(r"\b(?:AHU|CH|CT|FCU)-[A-Z]-[A-Z0-9]+-\d{2}\b", re.IGNORECASE)

WORK_ORDER_KEYWORDS = [
    "工单",
    "派单",
    "接单",
    "复核",
    "关闭",
    "闭环",
    "处理结果",
    "现场原因",
    "刚关闭",
    "最近关闭",
    "节能闭环",
    "处置",
    "维修",
]
BUDGET_KEYWORDS = ["预算", "KPI", "执行率", "超支"]
ROI_KEYWORDS = ["ROI", "回收期", "NPV", "IRR", "改造", "投资"]
SIM_KEYWORDS = ["时间机器", "仿真", "未来", "延迟", "不处理", "立即处理"]


def classify_assistant_question(question: str) -> Dict:
    text = str(question or "")
    lower = text.lower()
    categories = []
    if any(keyword.lower() in lower for keyword in WORK_ORDER_KEYWORDS):
        categories.append("work_orders")
    if any(keyword.lower() in lower for keyword in BUDGET_KEYWORDS):
        categories.append("budget")
    if any(keyword.lower() in lower for keyword in ROI_KEYWORDS):
        categories.append("roi")
    if any(keyword.lower() in lower for keyword in SIM_KEYWORDS):
        categories.append("simulation")

    explicit_entities = {
        "work_order_ids": sorted({item.upper() for item in WORK_ORDER_RE.findall(text)}),
        "equipment_ids": sorted({item.upper() for item in EQUIPMENT_RE.findall(text)}),
    }
    return {
        "question_type": categories[0] if categories else "knowledge",
        "categories": categories,
        "requires_work_order_grounding": "work_orders" in categories or bool(explicit_entities["work_order_ids"]),
        "explicit_entities": explicit_entities,
    }


def _status_label(order: Dict) -> str:
    return order.get("status_label") or order.get("status") or "-"


def _order_sort_key(order: Dict) -> tuple:
    return (
        str(order.get("closed_at") or order.get("updated_at") or order.get("created_at") or ""),
        str(order.get("timestamp") or ""),
    )


def _order_summary(order: Dict) -> Dict:
    return {
        "work_order_id": order.get("work_order_id", ""),
        "source_record_id": order.get("source_record_id", ""),
        "building_name": order.get("building_name", ""),
        "floor_label": order.get("floor_label", ""),
        "equipment_id": order.get("equipment_id", ""),
        "equipment_type": order.get("equipment_type", ""),
        "status": order.get("status", ""),
        "status_label": _status_label(order),
        "priority": order.get("priority", ""),
        "assignee_id": order.get("assignee_id", ""),
        "assignee_name": order.get("assignee_name", ""),
        "anomaly_reason": order.get("anomaly_reason", ""),
        "actual_cause": order.get("actual_cause", ""),
        "resolution_note": order.get("resolution_note", ""),
        "review_note": order.get("review_note", ""),
        "before_kwh": order.get("before_kwh"),
        "after_kwh": order.get("after_kwh"),
        "before_cop": order.get("before_cop"),
        "after_cop": order.get("after_cop"),
        "after_is_estimated": bool(order.get("after_is_estimated")),
        "wasted_kwh": order.get("wasted_kwh"),
        "wasted_cost_yuan": order.get("wasted_cost_yuan"),
        "estimated_saving_yuan": order.get("estimated_saving_yuan"),
        "carbon_kg": order.get("carbon_kg"),
        "sla_hours": order.get("sla_hours"),
        "created_at": order.get("created_at", ""),
        "updated_at": order.get("updated_at", ""),
        "closed_at": order.get("closed_at", ""),
        "timeline": [
            {
                "action": event.get("action", ""),
                "to_status": event.get("to_status", ""),
                "operator_id": event.get("operator_id", ""),
                "operator_name": event.get("operator_name", ""),
                "note": event.get("note", ""),
                "created_at": event.get("created_at", ""),
            }
            for event in (order.get("timeline") or [])[-4:]
        ],
    }


def build_work_order_grounding_context(question: str, max_orders: int = 6) -> Dict:
    classification = classify_assistant_question(question)
    orders = list_work_orders()
    if not classification["requires_work_order_grounding"]:
        return {
            "applies": False,
            "classification": classification,
            "orders": [],
            "entity_whitelist": _entity_whitelist(orders),
        }

    explicit_order_ids = set(classification["explicit_entities"]["work_order_ids"])
    explicit_equipment_ids = set(classification["explicit_entities"]["equipment_ids"])
    question_text = str(question or "")

    related = []
    for order in orders:
        wid = str(order.get("work_order_id", "")).upper()
        eid = str(order.get("equipment_id", "")).upper()
        building = str(order.get("building_name", ""))
        if wid in explicit_order_ids or eid in explicit_equipment_ids or (building and building in question_text):
            related.append(order)

    if not related:
        closed = [item for item in orders if item.get("status") == "closed"]
        open_orders = [item for item in orders if item.get("status") not in {"closed", "ignored"}]
        if "刚关闭" in question_text or "最近关闭" in question_text or "关闭" in question_text:
            related = sorted(closed, key=_order_sort_key, reverse=True)[:max_orders]
        else:
            related = sorted(open_orders, key=_order_sort_key, reverse=True)[: max_orders // 2]
            related += sorted(closed, key=_order_sort_key, reverse=True)[: max_orders - len(related)]

    related = related[:max_orders]
    return {
        "applies": True,
        "classification": classification,
        "orders": [_order_summary(item) for item in related],
        "entity_whitelist": _entity_whitelist(orders),
    }


def _entity_whitelist(orders: List[Dict]) -> Dict:
    return {
        "work_order_ids": sorted({str(item.get("work_order_id", "")).upper() for item in orders if item.get("work_order_id")}),
        "equipment_ids": sorted({str(item.get("equipment_id", "")).upper() for item in orders if item.get("equipment_id")}),
        "building_names": sorted({str(item.get("building_name", "")) for item in orders if item.get("building_name")}),
    }


def format_grounding_context_for_llm(context: Dict) -> str:
    if not context.get("applies") or not context.get("orders"):
        return ""

    lines = [
        "REAL_TIME_WORK_ORDER_CONTEXT:",
        "Only use these runtime work orders. Do not invent work_order_id, equipment_id, status, dates, cost, or savings.",
    ]
    for index, order in enumerate(context["orders"], start=1):
        timeline = " / ".join(
            f"{event.get('action')}->{event.get('to_status')}@{event.get('created_at')}"
            for event in order.get("timeline", [])
            if event.get("action")
        )
        lines.append(
            (
                f"{index}. work_order_id={order['work_order_id']}; "
                f"building={order['building_name']} {order['floor_label']}; "
                f"equipment_id={order['equipment_id']}; equipment_type={order['equipment_type']}; "
                f"status={order['status']}({order['status_label']}); priority={order['priority']}; "
                f"assignee={order['assignee_name'] or order['assignee_id']}; "
                f"anomaly_reason={order['anomaly_reason']}; "
                f"actual_cause={order['actual_cause'] or '未填写'}; "
                f"resolution={order['resolution_note'] or '未填写'}; "
                f"before_kwh={order['before_kwh']}; after_kwh={order['after_kwh']}; "
                f"before_cop={order['before_cop']}; after_cop={order['after_cop']}; "
                f"estimated_saving_yuan={order['estimated_saving_yuan']}; "
                f"wasted_cost_yuan={order['wasted_cost_yuan']}; carbon_kg={order['carbon_kg']}; "
                f"closed_at={order['closed_at'] or '未关闭'}; timeline={timeline or '暂无'}"
            )
        )
    return "\n".join(lines)


def validate_grounded_answer(answer: str, context: Dict) -> Dict:
    if not context.get("applies"):
        return {"valid": True, "warnings": [], "referenced_entities": {}}

    whitelist = context.get("entity_whitelist") or {}
    allowed_work_orders = set(whitelist.get("work_order_ids") or [])
    allowed_equipment = set(whitelist.get("equipment_ids") or [])
    allowed_buildings = set(whitelist.get("building_names") or [])
    text = str(answer or "")

    referenced_work_orders = sorted({item.upper() for item in WORK_ORDER_RE.findall(text)})
    referenced_equipment = sorted({item.upper() for item in EQUIPMENT_RE.findall(text)})
    referenced_buildings = sorted({name for name in allowed_buildings if name and name in text})

    warnings = []
    invalid_orders = [item for item in referenced_work_orders if item not in allowed_work_orders]
    invalid_equipment = [item for item in referenced_equipment if item not in allowed_equipment]
    if invalid_orders:
        warnings.append("外部模型回答引用了不存在的工单号：{0}".format("、".join(invalid_orders)))
    if invalid_equipment:
        warnings.append("外部模型回答引用了不存在的设备号：{0}".format("、".join(invalid_equipment)))

    # If the answer talks about an order but references no real entity at all, it is
    # too vague for a grounded work-order question.
    if context.get("orders") and not referenced_work_orders and not referenced_equipment:
        if any(keyword in text for keyword in ["工单", "设备", "闭环", "处理", "复核"]):
            warnings.append("外部模型回答未引用任何实时工单或设备实体。")

    return {
        "valid": not warnings,
        "warnings": warnings,
        "referenced_entities": {
            "work_order_ids": referenced_work_orders,
            "equipment_ids": referenced_equipment,
            "building_names": referenced_buildings,
        },
    }


def build_grounded_fallback_reply(question: str, context: Dict, local_reply: Dict) -> Dict:
    orders = context.get("orders") or []
    if not orders:
        return {
            **local_reply,
            "grounding_used": bool(context.get("applies")),
            "grounding_sources": ["work_orders"] if context.get("applies") else [],
            "grounding_status": "grounded" if context.get("applies") else "none",
            "validation_warnings": [],
            "referenced_entities": {},
        }

    order = orders[0]
    effect = ""
    if order.get("before_kwh") and order.get("after_kwh"):
        effect = (
            f"处理前后电耗 {order['before_kwh']} -> {order['after_kwh']} kWh"
            f"{'（估算）' if order.get('after_is_estimated') else ''}。"
        )
    economy = ""
    if order.get("estimated_saving_yuan") or order.get("wasted_cost_yuan"):
        economy = (
            f"该异常估算损失 {order.get('wasted_cost_yuan') or 0} 元，"
            f"处置后预计可回收 {order.get('estimated_saving_yuan') or 0} 元。"
        )
    timeline = "、".join(
        event.get("action", "")
        for event in order.get("timeline", [])
        if event.get("action")
    )
    answer = (
        f"基于实时工单数据，当前最相关工单是 {order['work_order_id']}，"
        f"设备 {order['equipment_id']}（{order['equipment_type']}），位置为"
        f"{order['building_name']} {order['floor_label']}，状态为{order['status_label']}。"
        f"现场原因：{order.get('actual_cause') or '尚未填写'}；"
        f"处理结果：{order.get('resolution_note') or '尚未填写'}。"
        f"{effect}{economy}"
    )
    if timeline:
        answer += f" 时间线已记录：{timeline}。"

    return {
        **local_reply,
        "answer": answer,
        "grounding_used": True,
        "grounding_sources": ["work_orders", "knowledge_base"],
        "grounding_status": "grounded",
        "validation_warnings": [],
        "referenced_entities": {
            "work_order_ids": [order["work_order_id"]],
            "equipment_ids": [order["equipment_id"]],
            "building_names": [order["building_name"]],
            "statuses": [order["status"]],
        },
    }
