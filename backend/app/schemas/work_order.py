from typing import Optional

from pydantic import BaseModel


class WorkOrderCreate(BaseModel):
    work_order_id: Optional[str] = None
    source_record_id: Optional[str] = None
    priority: str = "中"
    status: str = "处理中"
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
    note: Optional[str] = ""


class WorkOrderUpdate(BaseModel):
    status: Optional[str] = None
    note: Optional[str] = None
    owner_role: Optional[str] = None
