from fastapi import APIRouter, HTTPException

from app.schemas.work_order import WorkOrderCreate, WorkOrderUpdate
from app.services.work_order_store import (
    create_work_order,
    list_work_orders,
    update_work_order,
)


router = APIRouter()


@router.get("")
def get_persistent_work_orders():
    return {"items": list_work_orders()}


@router.post("")
def post_work_order(payload: WorkOrderCreate):
    return create_work_order(payload.model_dump())


@router.patch("/{work_order_id}")
def patch_work_order(work_order_id: str, payload: WorkOrderUpdate):
    updated = update_work_order(
        work_order_id,
        status=payload.status,
        note=payload.note,
        owner_role=payload.owner_role,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Work order not found")
    return updated
