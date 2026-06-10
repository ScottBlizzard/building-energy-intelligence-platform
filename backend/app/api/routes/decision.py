from typing import Optional

from fastapi import APIRouter

from app.services.decision_service import (
    find_roi_candidates_from_repeated_anomalies,
    rank_open_work_orders,
    recommend_dispatch_plan,
    summarize_budget_impact_from_closures,
)

router = APIRouter()


@router.get("/work-order-priorities")
def get_work_order_priorities(limit: int = 10):
    items = rank_open_work_orders(limit=limit)
    return {"items": items, "count": len(items)}


@router.get("/dispatch-plan")
def get_dispatch_plan(worker_capacity: int = 3):
    return {"item": recommend_dispatch_plan(worker_capacity=worker_capacity)}


@router.get("/budget-impact")
def get_budget_impact(year: Optional[int] = None, month: Optional[int] = None):
    return {"item": summarize_budget_impact_from_closures(year=year, month=month)}


@router.get("/roi-candidates")
def get_roi_candidates(limit: int = 8):
    items = find_roi_candidates_from_repeated_anomalies(limit=limit)
    return {"items": items, "count": len(items)}
