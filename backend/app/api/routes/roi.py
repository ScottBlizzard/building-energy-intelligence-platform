from fastapi import APIRouter, HTTPException

from app.schemas.roi import ROIProjectRequest, ROIScenarioCompare
from app.services.permission_service import PermissionDenied, require_admin_operator
from app.services.roi_service import analyze_roi_project, build_equipment_audit, compare_scenarios

router = APIRouter()


def _require_admin(operator_id: str = "admin") -> None:
    try:
        require_admin_operator(operator_id, "查看或调整 ROI 决策")
    except PermissionDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc))


@router.get("/audit/{building_id}")
def get_equipment_audit(building_id: str, operator_id: str = "admin"):
    _require_admin(operator_id)
    return {"item": build_equipment_audit(building_id)}


@router.post("/analyze")
def analyze_project(payload: ROIProjectRequest, operator_id: str = "admin"):
    _require_admin(operator_id)
    result = analyze_roi_project(payload.model_dump())
    return {"item": result}


@router.post("/compare")
def compare_roi_scenarios(payload: ROIScenarioCompare, operator_id: str = "admin"):
    _require_admin(operator_id)
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
