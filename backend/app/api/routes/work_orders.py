from typing import Optional

from fastapi import APIRouter, Header, HTTPException

from app.api.deps import require_admin_user, require_worker_user, resolve_operator_user
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
    EquipmentAlreadyHandledError,
    WorkerBusyError,
    accept_work_order,
    assign_work_order,
    create_work_order,
    create_work_order_from_anomaly,
    create_pending_confirm_drafts,
    ignore_work_order,
    list_work_orders,
    review_work_order,
    submit_work_order,
    update_work_order,
)


router = APIRouter()


def _admin(operator_id: str = "admin", authorization: str = "", action: str = "manage work orders"):
    return require_admin_user(operator_id=operator_id, authorization=authorization, action=action)


def _worker(operator_id: str = "", authorization: str = "", action: str = "process work orders"):
    return require_worker_user(operator_id=operator_id, authorization=authorization, action=action)


@router.get("")
def get_persistent_work_orders(
    assignee_id: Optional[str] = None,
    status: Optional[str] = None,
    role: Optional[str] = None,
    operator_id: str = "",
    authorization: str = Header(default=""),
):
    user = resolve_operator_user(
        operator_id=operator_id or None,
        authorization=authorization,
        fallback_user_id=assignee_id or "admin",
    )
    if user.get("role") == "worker":
        assignee_id = user["user_id"]
        role = "worker"
    return {"items": list_work_orders(assignee_id=assignee_id, status=status, role=role)}


@router.post("")
def post_work_order(payload: WorkOrderCreate, authorization: str = Header(default="")):
    data = payload.model_dump()
    operator = _admin(
        data.get("created_by") or "admin",
        authorization,
        action="create or confirm work orders",
    )
    data["created_by"] = operator["user_id"]
    if data.get("assignee_id"):
        try:
            return create_work_order_from_anomaly(data, operator_id=operator["user_id"])
        except (WorkerBusyError, EquipmentAlreadyHandledError) as exc:
            raise HTTPException(status_code=409, detail=str(exc))
    return create_work_order(data)


@router.post("/auto-confirm-queue")
def post_auto_confirm_queue(
    operator_id: str = "admin",
    authorization: str = Header(default=""),
):
    operator = _admin(operator_id, authorization, action="confirm anomaly work orders")
    from app.services.analysis_service import build_anomaly_work_order_drafts
    from app.services.data_loader import get_visible_dataset

    frame = get_visible_dataset()
    drafts = build_anomaly_work_order_drafts(frame)
    return create_pending_confirm_drafts(drafts, operator_id=operator["user_id"])


@router.patch("/{work_order_id}")
def patch_work_order(
    work_order_id: str,
    payload: WorkOrderUpdate,
    operator_id: str = "admin",
    authorization: str = Header(default=""),
):
    _admin(operator_id, authorization, action="update work orders")
    updated = update_work_order(
        work_order_id,
        status=payload.status,
        note=payload.note,
        owner_role=payload.owner_role,
        dispatch_action=payload.dispatch_action,
        resolution_action=payload.resolution_action,
        verification_result=payload.verification_result,
        verification_status=payload.verification_status,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Work order not found")
    return updated


@router.patch("/{work_order_id}/assign")
def patch_assign_work_order(
    work_order_id: str,
    payload: WorkOrderAssign,
    authorization: str = Header(default=""),
):
    operator = _admin(payload.operator_id, authorization, action="assign work orders")
    try:
        updated = assign_work_order(
            work_order_id,
            assignee_id=payload.assignee_id,
            operator_id=operator["user_id"],
            note=payload.note or "",
        )
    except WorkerBusyError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if not updated:
        raise HTTPException(status_code=404, detail="Work order or worker not found")
    return updated


@router.patch("/{work_order_id}/accept")
def patch_accept_work_order(
    work_order_id: str,
    payload: WorkOrderAccept,
    authorization: str = Header(default=""),
):
    operator = _worker(payload.operator_id, authorization, action="accept work orders")
    updated = accept_work_order(
        work_order_id,
        operator_id=operator["user_id"],
        note=payload.note or "",
    )
    if not updated:
        raise HTTPException(status_code=409, detail="Work order cannot be accepted")
    return updated


@router.patch("/{work_order_id}/submit")
def patch_submit_work_order(
    work_order_id: str,
    payload: WorkOrderSubmit,
    authorization: str = Header(default=""),
):
    operator = _worker(payload.operator_id, authorization, action="submit work order results")
    updated = submit_work_order(
        work_order_id,
        operator_id=operator["user_id"],
        actual_cause=payload.actual_cause,
        resolution_note=payload.resolution_note,
        recovery_confirmed=payload.recovery_confirmed,
        parts_used=payload.parts_used or "",
        safety_note=payload.safety_note or "",
        attachment_name=payload.attachment_name or "",
        attachment_note=payload.attachment_note or "",
        attachment_data=payload.attachment_data or "",
    )
    if not updated:
        raise HTTPException(status_code=409, detail="Work order cannot be submitted")
    return updated


@router.patch("/{work_order_id}/review")
def patch_review_work_order(
    work_order_id: str,
    payload: WorkOrderReview,
    authorization: str = Header(default=""),
):
    operator = _admin(payload.operator_id, authorization, action="review work orders")
    updated = review_work_order(
        work_order_id,
        operator_id=operator["user_id"],
        approved=payload.approved,
        review_note=payload.review_note or "",
    )
    if not updated:
        raise HTTPException(status_code=409, detail="Work order cannot be reviewed")
    return updated


@router.patch("/{work_order_id}/ignore")
def patch_ignore_work_order(
    work_order_id: str,
    payload: WorkOrderIgnore,
    authorization: str = Header(default=""),
):
    operator = _admin(payload.operator_id, authorization, action="ignore work orders")
    updated = ignore_work_order(
        work_order_id,
        operator_id=operator["user_id"],
        note=payload.note or "",
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Work order not found")
    return updated
