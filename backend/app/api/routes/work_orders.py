from typing import Optional

from fastapi import APIRouter, HTTPException

from app.schemas.work_order import (
    WorkOrderAccept,
    WorkOrderAssign,
    WorkOrderCreate,
    WorkOrderIgnore,
    WorkOrderReview,
    WorkOrderSubmit,
    WorkOrderUpdate,
)
from app.services.work_order_store import (
    accept_work_order,
    assign_work_order,
    create_work_order,
    create_work_order_from_anomaly,
    ignore_work_order,
    list_work_orders,
    review_work_order,
    submit_work_order,
    update_work_order,
)


router = APIRouter()


@router.get("")
def get_persistent_work_orders(
    assignee_id: Optional[str] = None,
    status: Optional[str] = None,
    role: Optional[str] = None,
):
    return {"items": list_work_orders(assignee_id=assignee_id, status=status, role=role)}


@router.post("")
def post_work_order(payload: WorkOrderCreate):
    data = payload.model_dump()
    if data.get("assignee_id"):
        return create_work_order_from_anomaly(data, operator_id=data.get("created_by") or "admin")
    return create_work_order(data)


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


@router.patch("/{work_order_id}/assign")
def patch_assign_work_order(work_order_id: str, payload: WorkOrderAssign):
    updated = assign_work_order(
        work_order_id,
        assignee_id=payload.assignee_id,
        operator_id=payload.operator_id,
        note=payload.note or "",
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Work order or worker not found")
    return updated


@router.patch("/{work_order_id}/accept")
def patch_accept_work_order(work_order_id: str, payload: WorkOrderAccept):
    updated = accept_work_order(
        work_order_id,
        operator_id=payload.operator_id,
        note=payload.note or "",
    )
    if not updated:
        raise HTTPException(status_code=409, detail="Work order cannot be accepted")
    return updated


@router.patch("/{work_order_id}/submit")
def patch_submit_work_order(work_order_id: str, payload: WorkOrderSubmit):
    updated = submit_work_order(
        work_order_id,
        operator_id=payload.operator_id,
        actual_cause=payload.actual_cause,
        resolution_note=payload.resolution_note,
        recovery_confirmed=payload.recovery_confirmed,
        parts_used=payload.parts_used or "",
        safety_note=payload.safety_note or "",
    )
    if not updated:
        raise HTTPException(status_code=409, detail="Work order cannot be submitted")
    return updated


@router.patch("/{work_order_id}/review")
def patch_review_work_order(work_order_id: str, payload: WorkOrderReview):
    updated = review_work_order(
        work_order_id,
        operator_id=payload.operator_id,
        approved=payload.approved,
        review_note=payload.review_note or "",
    )
    if not updated:
        raise HTTPException(status_code=409, detail="Work order cannot be reviewed")
    return updated


@router.patch("/{work_order_id}/ignore")
def patch_ignore_work_order(work_order_id: str, payload: WorkOrderIgnore):
    updated = ignore_work_order(
        work_order_id,
        operator_id=payload.operator_id,
        note=payload.note or "",
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Work order not found")
    return updated
