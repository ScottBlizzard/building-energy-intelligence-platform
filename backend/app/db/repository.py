from __future__ import annotations

from typing import Dict, List, Optional

from sqlalchemy import delete, inspect, select

from app.db.engine import get_engine, get_session, is_db_enabled
from app.db.models import Base, BudgetRow, SimStateRow, WorkOrderRow


def is_enabled() -> bool:
    return is_db_enabled()


def ensure_schema() -> None:
    """惰性建表（幂等）。首次读写时自动创建缺失的业务表。"""
    Base.metadata.create_all(get_engine())


# --------------------------------------------------------------------------- #
# 工单
# --------------------------------------------------------------------------- #
def read_work_orders() -> List[Dict]:
    ensure_schema()
    with get_session() as session:
        rows = (
            session.execute(select(WorkOrderRow).order_by(WorkOrderRow.pos))
            .scalars()
            .all()
        )
        return [dict(row.data) for row in rows if row.data is not None]


def write_work_orders(items: List[Dict]) -> None:
    ensure_schema()
    with get_session() as session:
        session.execute(delete(WorkOrderRow))
        for pos, item in enumerate(items):
            session.add(
                WorkOrderRow(
                    work_order_id=str(item.get("work_order_id") or f"wo_{pos}"),
                    pos=pos,
                    status=str(item.get("status") or ""),
                    assignee_id=str(item.get("assignee_id") or ""),
                    building_id=str(item.get("building_id") or ""),
                    equipment_id=str(item.get("equipment_id") or ""),
                    priority=str(item.get("priority") or ""),
                    source_record_id=str(item.get("source_record_id") or ""),
                    created_at=str(item.get("created_at") or ""),
                    timestamp=str(item.get("timestamp") or ""),
                    data=item,
                )
            )
        session.commit()


# --------------------------------------------------------------------------- #
# 预算
# --------------------------------------------------------------------------- #
def read_budgets() -> List[Dict]:
    ensure_schema()
    with get_session() as session:
        rows = (
            session.execute(select(BudgetRow).order_by(BudgetRow.pos)).scalars().all()
        )
        return [dict(row.data) for row in rows if row.data is not None]


def write_budgets(items: List[Dict]) -> None:
    ensure_schema()
    with get_session() as session:
        session.execute(delete(BudgetRow))
        for pos, item in enumerate(items):
            session.add(
                BudgetRow(
                    pos=pos,
                    building_id=str(item.get("building_id") or ""),
                    year=int(item.get("year") or 0),
                    month=int(item.get("month") or 0),
                    budget_kwh=float(item.get("budget_kwh") or 0.0),
                    data=item,
                )
            )
        session.commit()


# --------------------------------------------------------------------------- #
# 时间沙盘状态
# --------------------------------------------------------------------------- #
def read_sim_state() -> Optional[Dict]:
    ensure_schema()
    with get_session() as session:
        row = session.get(SimStateRow, 1)
        if row is None or row.data is None:
            return None
        return dict(row.data)


def write_sim_state(state: Dict) -> None:
    ensure_schema()
    with get_session() as session:
        row = session.get(SimStateRow, 1)
        if row is None:
            row = SimStateRow(id=1)
            session.add(row)
        row.sim_current_date = state.get("current_date")
        row.sim_start_date = state.get("start_date")
        row.data = state
        session.commit()


# --------------------------------------------------------------------------- #
# 能耗读数（原始数据集）
# --------------------------------------------------------------------------- #
def has_energy_readings() -> bool:
    engine = get_engine()
    if not inspect(engine).has_table("energy_readings"):
        return False
    import pandas as pd

    count = pd.read_sql("SELECT COUNT(*) AS n FROM energy_readings", engine)
    return int(count.iloc[0]["n"]) > 0


def read_energy_dataframe():
    """从数据库读取能耗读数为 DataFrame；表不存在或为空返回 None。"""
    import pandas as pd

    engine = get_engine()
    if not inspect(engine).has_table("energy_readings"):
        return None
    frame = pd.read_sql_table("energy_readings", engine)
    if frame.empty:
        return None
    return frame
