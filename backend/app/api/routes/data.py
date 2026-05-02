from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.analysis_service import build_overview, to_serializable_records
from app.services.data_loader import (
    get_building_options,
    get_dataset_meta,
    load_dataset_or_raise,
)


router = APIRouter()


@router.get("/overview")
def get_overview():
    frame = load_dataset_or_raise()
    return build_overview(frame)


@router.get("/dataset-meta")
def get_data_meta():
    try:
        return get_dataset_meta()
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/buildings")
def get_buildings():
    try:
        return {"items": get_building_options()}
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/records")
def get_records(
    building_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(default=100, ge=1, le=500),
):
    frame = load_dataset_or_raise(
        building_id=building_id, start_time=start_time, end_time=end_time
    )
    limited = frame.head(limit)
    return {
        "count": int(len(limited)),
        "total_filtered_count": int(len(frame)),
        "items": to_serializable_records(limited),
    }
