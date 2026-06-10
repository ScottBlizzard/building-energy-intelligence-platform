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


class WorkOrderUpdate(BaseModel):
    status: Optional[str] = None
    note: Optional[str] = None
    owner_role: Optional[str] = None


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
