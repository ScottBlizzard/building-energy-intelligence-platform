from typing import List, Optional

from pydantic import BaseModel


class ROIProjectRequest(BaseModel):
    building_id: str
    equipment_type: str
    investment_yuan: float
    expected_cop_improvement: Optional[float] = None
    expected_saving_pct: Optional[float] = None
    project_lifespan_years: Optional[int] = None
    project_name: Optional[str] = ""
    annual_maintenance_cost: Optional[float] = 0
    discount_rate: Optional[float] = None
    investment_basis: Optional[str] = None


class ROIScenarioCompare(BaseModel):
    building_id: str
    scenarios: List[ROIProjectRequest]
