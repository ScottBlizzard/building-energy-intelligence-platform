from fastapi import APIRouter

from app.services.admin_dashboard_service import build_admin_dashboard, worker_dashboard


router = APIRouter()


@router.get("/dashboard")
def get_admin_dashboard():
    return {"item": build_admin_dashboard()}


@router.get("/worker-dashboard/{user_id}")
def get_worker_dashboard(user_id: str):
    return {"item": worker_dashboard(user_id)}
