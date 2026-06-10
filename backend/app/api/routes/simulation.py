from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.services import simulation_service
from app.services.data_loader import get_dataset_meta
from app.services.scenario_service import build_counterfactual_scenarios

router = APIRouter()


class SimStart(BaseModel):
    start_date: Optional[str] = None


class SimAdvance(BaseModel):
    days: int = 1


class CounterfactualRequest(BaseModel):
    equipment_id: str
    horizon_days: int = 7
    delay_days: int = 3
    start_date: Optional[str] = None


def _state_with_range() -> dict:
    state = simulation_service.get_state()
    meta = get_dataset_meta()
    state["data_range"] = meta.get("time_range", {})
    return state


@router.get("/state")
def get_sim_state():
    return _state_with_range()


@router.post("/start")
def start_sim(payload: SimStart):
    simulation_service.start_simulation(payload.start_date)
    return _state_with_range()


@router.post("/advance")
def advance_sim(payload: SimAdvance):
    simulation_service.advance_day(payload.days)
    return _state_with_range()


@router.post("/reset")
def reset_sim():
    simulation_service.reset()
    return _state_with_range()


@router.post("/counterfactual")
def counterfactual(payload: CounterfactualRequest):
    return {
        "item": build_counterfactual_scenarios(
            payload.equipment_id,
            horizon_days=payload.horizon_days,
            delay_days=payload.delay_days,
            start_date=payload.start_date,
        )
    }
