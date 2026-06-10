from fastapi import APIRouter, HTTPException

from app.services.anomaly_event_service import build_anomaly_event


router = APIRouter()


@router.get("/{record_id}")
def get_anomaly_event(record_id: str):
    item = build_anomaly_event(record_id)
    if not item:
        raise HTTPException(status_code=404, detail="Anomaly event not found")
    return {"item": item}
