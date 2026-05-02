from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.services.export_service import build_csv_content, build_export_filename
from io import StringIO


router = APIRouter()


@router.get("/csv")
def export_csv(
    building_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
):
    """Export filtered records as a CSV file download."""
    try:
        csv_content = build_csv_content(
            building_id=building_id, start_time=start_time, end_time=end_time
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if not csv_content:
        raise HTTPException(status_code=404, detail="No records found for the given filters.")

    filename = build_export_filename(building_id)
    return StreamingResponse(
        StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename={0}".format(filename)},
    )
