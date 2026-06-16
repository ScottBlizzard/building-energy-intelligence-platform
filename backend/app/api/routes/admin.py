from fastapi import APIRouter, Header, HTTPException

from app.api.deps import require_admin_user, resolve_operator_user
from app.services.admin_dashboard_service import build_admin_dashboard, worker_dashboard


router = APIRouter()


@router.get("/dashboard")
def get_admin_dashboard(
    operator_id: str = "admin",
    authorization: str = Header(default=""),
):
    require_admin_user(
        operator_id=operator_id,
        authorization=authorization,
        action="view the admin dashboard",
    )
    return {"item": build_admin_dashboard()}


@router.get("/worker-dashboard/{user_id}")
def get_worker_dashboard(
    user_id: str,
    operator_id: str = "",
    authorization: str = Header(default=""),
):
    user = resolve_operator_user(
        operator_id=operator_id or None,
        authorization=authorization,
        fallback_user_id=user_id,
    )
    if user.get("role") != "admin" and user.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Workers can only view their own dashboard.")
    return {"item": worker_dashboard(user_id)}
