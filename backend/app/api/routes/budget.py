from typing import Optional

from fastapi import APIRouter

from app.schemas.budget import BudgetAdjust, BudgetSet
from app.services.budget_service import (
    auto_generate_budgets,
    build_budget_analysis,
    build_budget_kpi,
    list_budgets,
    set_budget,
)

router = APIRouter()


@router.get("/budgets")
def get_budgets(year: Optional[int] = None, month: Optional[int] = None):
    return {"items": list_budgets(year=year, month=month)}


@router.post("/budgets/generate")
def generate_budgets(year: int, month: int):
    items = auto_generate_budgets(year, month)
    return {"items": items, "count": len(items)}


@router.post("/budgets")
def create_or_update_budget(payload: BudgetSet):
    result = set_budget(payload.model_dump())
    return {"item": result}


@router.get("/budgets/analysis")
def get_budget_analysis(year: int, month: int):
    return {"item": build_budget_analysis(year, month)}


@router.get("/budgets/kpi/{building_id}")
def get_budget_kpi(building_id: str, year: int):
    return {"item": build_budget_kpi(building_id, year)}
