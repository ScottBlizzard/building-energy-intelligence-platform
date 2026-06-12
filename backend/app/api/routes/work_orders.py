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
from app.services.permission_service import PermissionDenied, require_admin_operator, require_worker_operator
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


def _raise_for_permission(exc: PermissionDenied) -> None:
    raise HTTPException(status_code=403, detail=str(exc))


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
    try:
        require_admin_operator(data.get("created_by") or "admin", "创建或确认工单")
    except PermissionDenied as exc:
        _raise_for_permission(exc)
    if data.get("assignee_id"):
        try:
            return create_work_order_from_anomaly(data, operator_id=data.get("created_by") or "admin")
        except (WorkerBusyError, EquipmentAlreadyHandledError) as exc:
            raise HTTPException(status_code=409, detail=str(exc))
    return create_work_order(data)


@router.post("/auto-confirm-queue")
def post_auto_confirm_queue():
    from app.services.analysis_service import build_anomaly_work_order_drafts
    from app.services.data_loader import get_visible_dataset
    frame = get_visible_dataset()
    drafts = build_anomaly_work_order_drafts(frame)
    result = create_pending_confirm_drafts(drafts, operator_id="admin")
    return result


@router.patch("/{work_order_id}")
def patch_work_order(work_order_id: str, payload: WorkOrderUpdate):
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
def patch_assign_work_order(work_order_id: str, payload: WorkOrderAssign):
    try:
        require_admin_operator(payload.operator_id, "派单")
    except PermissionDenied as exc:
        _raise_for_permission(exc)
    try:
        updated = assign_work_order(
            work_order_id,
            assignee_id=payload.assignee_id,
            operator_id=payload.operator_id,
            note=payload.note or "",
        )
    except WorkerBusyError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if not updated:
        raise HTTPException(status_code=404, detail="Work order or worker not found")
    return updated


@router.patch("/{work_order_id}/accept")
def patch_accept_work_order(work_order_id: str, payload: WorkOrderAccept):
    try:
        require_worker_operator(payload.operator_id, "接收工单")
    except PermissionDenied as exc:
        _raise_for_permission(exc)
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
    try:
        require_worker_operator(payload.operator_id, "提交工单处理结果")
    except PermissionDenied as exc:
        _raise_for_permission(exc)
    updated = submit_work_order(
        work_order_id,
        operator_id=payload.operator_id,
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
def patch_review_work_order(work_order_id: str, payload: WorkOrderReview):
    try:
        require_admin_operator(payload.operator_id, "复核工单")
    except PermissionDenied as exc:
        _raise_for_permission(exc)
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
    try:
        require_admin_operator(payload.operator_id, "忽略工单")
    except PermissionDenied as exc:
        _raise_for_permission(exc)
    updated = ignore_work_order(
        work_order_id,
        operator_id=payload.operator_id,
        note=payload.note or "",
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Work order not found")
    return updated
