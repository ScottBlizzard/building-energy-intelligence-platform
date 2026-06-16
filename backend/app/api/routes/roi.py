from fastapi import APIRouter, Header

from app.api.deps import require_admin_user
from app.schemas.roi import ROIProjectRequest, ROIScenarioCompare
from app.services.roi_service import analyze_roi_project, build_equipment_audit, compare_scenarios

router = APIRouter()


def _require_admin(operator_id: str = "admin", authorization: str = "") -> None:
    require_admin_user(
        operator_id=operator_id,
        authorization=authorization,
        action="view or adjust ROI decisions",
    )


@router.get("/audit/{building_id}")
def get_equipment_audit(
    building_id: str,
    operator_id: str = "admin",
    authorization: str = Header(default=""),
):
    _require_admin(operator_id, authorization)
    return {"item": build_equipment_audit(building_id)}


@router.post("/analyze")
def analyze_project(
    payload: ROIProjectRequest,
    operator_id: str = "admin",
    authorization: str = Header(default=""),
):
    _require_admin(operator_id, authorization)
    result = analyze_roi_project(payload.model_dump())
    return {"item": result}


@router.post("/compare")
def compare_roi_scenarios(
    payload: ROIScenarioCompare,
    operator_id: str = "admin",
    authorization: str = Header(default=""),
):
    _require_admin(operator_id, authorization)
    result = compare_scenarios(payload.model_dump())
    return {"item": result}


@router.get("/roi/audit/{building_id}", include_in_schema=False)
def get_equipment_audit_legacy(building_id: str):
    return {"item": build_equipment_audit(building_id)}


@router.post("/roi/analyze", include_in_schema=False)
def analyze_project_legacy(payload: ROIProjectRequest):
    return {"item": analyze_roi_project(payload.model_dump())}


@router.post("/roi/compare", include_in_schema=False)
def compare_roi_scenarios_legacy(payload: ROIScenarioCompare):
    return {"item": compare_scenarios(payload.model_dump())}
