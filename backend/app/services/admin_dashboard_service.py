from __future__ import annotations

from typing import Dict, List

from app.services.analysis_service import (
    build_anomaly_summary,
    build_floor_registry,
    build_optimization_recommendations,
)
from app.services.data_loader import get_visible_dataset
from app.services.work_order_store import build_work_order_metrics, list_work_orders


def build_admin_dashboard() -> Dict:
    frame = get_visible_dataset()
    anomalies = build_anomaly_summary(frame)
    floors = build_floor_registry(frame)
    recommendations = build_optimization_recommendations(frame)
    work_orders = list_work_orders()
    metrics = build_work_order_metrics(work_orders)

    high_risk_floors = [
        item for item in floors if item.get("risk_level") in {"高风险", "关注"}
    ][:6]
    pending_review = [
        item for item in work_orders if item.get("status") == "pending_review"
    ][:6]
    high_priority_open = [
        item
        for item in work_orders
        if item.get("priority") == "高" and item.get("status") not in {"closed", "ignored"}
    ][:6]

    return {
        "kpis": {
            "today_anomaly_count": len(anomalies),
            "open_work_order_count": metrics["open_count"],
            "pending_review_count": metrics["pending_review_count"],
            "closed_work_order_count": metrics["closed_count"],
            "high_priority_open_count": metrics["high_priority_open_count"],
        },
        "work_order_metrics": metrics,
        "latest_anomalies": anomalies[:6],
        "pending_review": pending_review,
        "high_priority_open": high_priority_open,
        "high_risk_floors": high_risk_floors,
        "recommendations": recommendations[:4],
        "next_actions": [
            "复核待复核工单，及时关闭已恢复问题。",
            "为高风险异常派单，避免停留在监测告警阶段。",
            "检查高风险楼层的 AHU、CH、CT 和 FCU 设备状态。",
            "将已关闭工单纳入今日运营日报。",
        ],
    }


def worker_dashboard(user_id: str) -> Dict:
    orders = list_work_orders(assignee_id=user_id)
    metrics = build_work_order_metrics(orders)
    needs_attention = [
        item for item in orders
        if item["status"] in {"assigned", "rejected"}
    ]
    return {
        "kpis": {
            "assigned_count": len([item for item in orders if item["status"] == "assigned"]),
            "in_progress_count": len([item for item in orders if item["status"] == "in_progress"]),
            "pending_review_count": len([item for item in orders if item["status"] == "pending_review"]),
            "closed_count": len([item for item in orders if item["status"] == "closed"]),
        },
        "work_order_metrics": metrics,
        "items": orders,
        "needs_attention": len(needs_attention),
        "next_actions": [
            "先接收已派单任务。",
            "处理中的工单尽快完成并提交复核。",
            "被驳回任务请根据复核意见补充处置。",
        ],
    }
