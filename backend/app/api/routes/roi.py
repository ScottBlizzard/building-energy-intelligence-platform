from fastapi import APIRouter

from app.schemas.roi import ROIProjectRequest, ROIScenarioCompare
from app.services.roi_service import analyze_roi_project, build_equipment_audit, compare_scenarios

router = APIRouter()


@router.get("/audit/{building_id}")
def get_equipment_audit(building_id: str):
    return {"item": build_equipment_audit(building_id)}


@router.post("/analyze")
def analyze_project(payload: ROIProjectRequest):
    result = analyze_roi_project(payload.model_dump())
    return {"item": result}


@router.post("/compare")
def compare_roi_scenarios(payload: ROIScenarioCompare):
    result = compare_scenarios(payload.model_dump())
    return {"item": result}


@router.get("/roi/audit/{building_id}", include_in_schema=False)
def get_equipment_audit_legacy(building_id: str):
    return get_equipment_audit(building_id)


@router.post("/roi/analyze", include_in_schema=False)
def analyze_project_legacy(payload: ROIProjectRequest):
    return analyze_project(payload)


@router.post("/roi/compare", include_in_schema=False)
def compare_roi_scenarios_legacy(payload: ROIScenarioCompare):
    return compare_roi_scenarios(payload)
