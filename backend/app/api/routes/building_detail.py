from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.building_detail_service import build_building_detail


router = APIRouter()


@router.get("/building-detail")
def get_building_detail(
    building_id: str = Query(..., description="建筑 ID，必填"),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
):
    """返回指定建筑的深度分析信息。"""
    try:
        result = build_building_detail(
            building_id=building_id, start_time=start_time, end_time=end_time
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if result["building_name"] is None:
        raise HTTPException(
            status_code=404,
            detail="No data found for building_id={0}".format(building_id),
        )

    return result
