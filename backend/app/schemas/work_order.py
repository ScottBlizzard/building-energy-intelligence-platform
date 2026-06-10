from typing import Optional

from pydantic import BaseModel


class WorkOrderCreate(BaseModel):
    work_order_id: Optional[str] = None
    source_record_id: Optional[str] = None
    priority: str = "中"
    status: Optional[str] = None
    building_id: str
    building_name: str
    floor_label: str
    zone_name: str
    equipment_id: str
    equipment_type: str
    timestamp: str
    anomaly_reason: str
    possible_cause: str
    recommended_action: str
    owner_role: str
    assignee_id: Optional[str] = None
    assignee_name: Optional[str] = None
    created_by: Optional[str] = None
    note: Optional[str] = ""
    before_kwh: Optional[float] = None
    before_cop: Optional[float] = None
    severity: Optional[str] = None
    risk_score: Optional[float] = None
    triggered_rule_count: Optional[int] = None
    wasted_kwh: Optional[float] = None
    wasted_cost_yuan: Optional[float] = None
    carbon_kg: Optional[float] = None
    estimated_saving_yuan: Optional[float] = None
    sla_hours: Optional[int] = None
    business_impact_summary: Optional[str] = None
    verification_method: Optional[str] = None
    verification_status: Optional[str] = None
    dispatch_action: Optional[str] = None
    resolution_action: Optional[str] = None
    verification_result: Optional[str] = None


class WorkOrderUpdate(BaseModel):
    status: Optional[str] = None
    note: Optional[str] = None
    owner_role: Optional[str] = None
    dispatch_action: Optional[str] = None
    resolution_action: Optional[str] = None
    verification_result: Optional[str] = None
    verification_status: Optional[str] = None


class WorkOrderAssign(BaseModel):
    assignee_id: str
    note: Optional[str] = ""
    operator_id: str = "admin"


class WorkOrderAccept(BaseModel):
    operator_id: str
    note: Optional[str] = ""


class WorkOrderSubmit(BaseModel):
    operator_id: str
    actual_cause: str
    resolution_note: str
    recovery_confirmed: bool = True
    parts_used: Optional[str] = ""
    safety_note: Optional[str] = ""
    attachment_name: Optional[str] = ""
    attachment_note: Optional[str] = ""


class WorkOrderReview(BaseModel):
    operator_id: str = "admin"
    approved: bool
    review_note: Optional[str] = ""


class WorkOrderIgnore(BaseModel):
    operator_id: str = "admin"
    note: Optional[str] = ""
