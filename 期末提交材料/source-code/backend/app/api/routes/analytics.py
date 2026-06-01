from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query

from app.services.analysis_service import (
    build_analysis_frame,
    build_anomaly_work_orders,
    build_anomaly_summary,
    build_anomaly_reason_counts,
    build_building_comparison,
    build_cop_ranking,
    build_equipment_summary,
    build_anomaly_explanation,
    build_floor_registry,
    build_operation_report,
    filter_display_frame_by_floor,
    build_floor_summary,
    build_optimization_recommendations,
    build_time_summary,
)
from app.services.data_loader import load_dataset_or_raise
from app.services.work_order_store import list_work_orders


router = APIRouter()


def _load_analytics_frame(
    building_id: Optional[str] = None,
    floor_label: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
):
    frame = build_analysis_frame(
        load_dataset_or_raise(
            building_id=building_id, start_time=start_time, end_time=end_time
        )
    )
    if floor_label:
        frame = filter_display_frame_by_floor(frame, floor_label)
    return frame


@router.get("/time-summary")
def get_time_summary(
    building_id: Optional[str] = None,
    floor_label: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    freq: str = Query(default="D", pattern="^(H|D|W|M)$"),
):
    frame = _load_analytics_frame(
        building_id=building_id,
        floor_label=floor_label,
        start_time=start_time,
        end_time=end_time,
    )
    return {"items": build_time_summary(frame, freq=freq)}


@router.get("/building-comparison")
def get_building_comparison(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
):
    frame = load_dataset_or_raise(start_time=start_time, end_time=end_time)
    return {"items": build_building_comparison(frame)}


@router.get("/cop-ranking")
def get_cop_ranking(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
):
    frame = load_dataset_or_raise(start_time=start_time, end_time=end_time)
    return {"items": build_cop_ranking(frame)}


@router.get("/anomalies")
def get_anomalies(
    building_id: Optional[str] = None,
    floor_label: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
):
    frame = _load_analytics_frame(
        building_id=building_id,
        floor_label=floor_label,
        start_time=start_time,
        end_time=end_time,
    )
    return {"items": build_anomaly_summary(frame)}


@router.get("/anomaly-explanations/{record_id}")
def get_anomaly_explanation(record_id: str):
    frame = build_analysis_frame(load_dataset_or_raise())
    explanation = build_anomaly_explanation(frame, record_id)
    if not explanation:
        return {"item": None}
    return {"item": explanation}


@router.get("/anomaly-reasons")
def get_anomaly_reasons(
    building_id: Optional[str] = None,
    floor_label: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
):
    frame = _load_analytics_frame(
        building_id=building_id,
        floor_label=floor_label,
        start_time=start_time,
        end_time=end_time,
    )
    return {"items": build_anomaly_reason_counts(frame)}


@router.get("/floor-summary")
def get_floor_summary(
    building_id: Optional[str] = None,
    floor_label: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
):
    frame = _load_analytics_frame(
        building_id=building_id,
        floor_label=floor_label,
        start_time=start_time,
        end_time=end_time,
    )
    return {"items": build_floor_summary(frame)}


@router.get("/floor-registry")
def get_floor_registry(
    building_id: Optional[str] = None,
    floor_label: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
):
    frame = _load_analytics_frame(
        building_id=building_id,
        floor_label=floor_label,
        start_time=start_time,
        end_time=end_time,
    )
    return {"items": build_floor_registry(frame)}


@router.get("/equipment-summary")
def get_equipment_summary(
    building_id: Optional[str] = None,
    floor_label: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
):
    frame = _load_analytics_frame(
        building_id=building_id,
        floor_label=floor_label,
        start_time=start_time,
        end_time=end_time,
    )
    return {"items": build_equipment_summary(frame)}


@router.get("/work-orders")
def get_work_orders(
    building_id: Optional[str] = None,
    floor_label: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
):
    frame = _load_analytics_frame(
        building_id=building_id,
        floor_label=floor_label,
        start_time=start_time,
        end_time=end_time,
    )
    return {"items": build_anomaly_work_orders(frame)}


@router.get("/optimization-recommendations")
def get_optimization_recommendations(
    building_id: Optional[str] = None,
    floor_label: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
):
    frame = _load_analytics_frame(
        building_id=building_id,
        floor_label=floor_label,
        start_time=start_time,
        end_time=end_time,
    )
    return {"items": build_optimization_recommendations(frame)}


@router.get("/operation-report")
def get_operation_report(
    building_id: Optional[str] = None,
    floor_label: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
):
    frame = _load_analytics_frame(
        building_id=building_id,
        floor_label=floor_label,
        start_time=start_time,
        end_time=end_time,
    )
    return {"item": build_operation_report(frame, list_work_orders())}
