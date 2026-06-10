from __future__ import annotations

from typing import Dict, Optional

from app.services.analysis_service import (
    build_analysis_frame,
    build_anomaly_explanation,
    build_anomaly_summary,
    build_equipment_summary,
)
from app.services.data_loader import get_visible_dataset
from app.services.work_order_store import list_work_orders


def build_anomaly_event(record_id: str) -> Optional[Dict]:
    frame = build_analysis_frame(get_visible_dataset())
    explanation = build_anomaly_explanation(frame, record_id)
    if not explanation:
        return None

    anomalies = build_anomaly_summary(frame)
    anomaly = next((item for item in anomalies if item["record_id"] == record_id), None)
    equipment = next(
        (
            item
            for item in build_equipment_summary(frame)
            if item["equipment_id"] == explanation["equipment_id"]
        ),
        None,
    )
    linked_orders = [
        item for item in list_work_orders() if item.get("source_record_id") == record_id
    ]

    return {
        "event_id": record_id,
        "record_id": record_id,
        "anomaly": anomaly,
        "explanation": explanation,
        "equipment": equipment,
        "linked_work_orders": linked_orders,
        "timeline": linked_orders[0].get("timeline", []) if linked_orders else [],
        "next_action": (
            "已有工单，继续跟踪处理状态。"
            if linked_orders
            else "建议管理员确认异常并生成工单。"
        ),
    }
