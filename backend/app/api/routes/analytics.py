from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query

from app.services.analysis_service import (
    build_anomaly_summary,
    build_anomaly_reason_counts,
    build_building_comparison,
    build_cop_ranking,
    build_time_summary,
)
from app.services.data_loader import load_dataset_or_raise


router = APIRouter()


@router.get("/time-summary")
def get_time_summary(
    building_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    freq: str = Query(default="D", pattern="^(H|D|W|M)$"),
):
    frame = load_dataset_or_raise(
        building_id=building_id, start_time=start_time, end_time=end_time
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
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
):
    frame = load_dataset_or_raise(
        building_id=building_id, start_time=start_time, end_time=end_time
    )
    return {"items": build_anomaly_summary(frame)}


@router.get("/anomaly-reasons")
def get_anomaly_reasons(
    building_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
):
    frame = load_dataset_or_raise(
        building_id=building_id, start_time=start_time, end_time=end_time
    )
    return {"items": build_anomaly_reason_counts(frame)}
