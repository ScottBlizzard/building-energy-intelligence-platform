from typing import Optional

from pydantic import BaseModel


class BudgetSet(BaseModel):
    building_id: str
    year: int
    month: int
    budget_kwh: float
    note: Optional[str] = ""


class BudgetAdjust(BaseModel):
    budget_kwh: float
    note: Optional[str] = ""
