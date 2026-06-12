from __future__ import annotations

from typing import Optional

from sqlalchemy import JSON, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class WorkOrderRow(Base):
    """工单表。

    可检索字段单独建列并加索引，完整的规范化字典保存在 ``data`` JSON 列里，
    从而既保留与原 JSON 存储完全一致的对象结构，又能用 SQL 高效过滤/统计。
    ``pos`` 用于保持与文件存储一致的插入顺序。
    """

    __tablename__ = "work_orders"

    work_order_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    pos: Mapped[int] = mapped_column(Integer, default=0, index=True)
    status: Mapped[str] = mapped_column(String(32), default="", index=True)
    assignee_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    building_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    equipment_id: Mapped[str] = mapped_column(String(64), default="")
    priority: Mapped[str] = mapped_column(String(16), default="")
    source_record_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    created_at: Mapped[str] = mapped_column(String(40), default="")
    timestamp: Mapped[str] = mapped_column(String(40), default="")
    data: Mapped[dict] = mapped_column(JSON)


class BudgetRow(Base):
    """月度预算表。"""

    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pos: Mapped[int] = mapped_column(Integer, default=0, index=True)
    building_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    year: Mapped[int] = mapped_column(Integer, default=0, index=True)
    month: Mapped[int] = mapped_column(Integer, default=0, index=True)
    budget_kwh: Mapped[float] = mapped_column(Float, default=0.0)
    data: Mapped[dict] = mapped_column(JSON)


class SimStateRow(Base):
    """时间沙盘状态表（单行，id 恒为 1）。"""

    __tablename__ = "sim_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 注意：避免使用 MySQL 保留字 current_date/start_date 作为列名。
    sim_current_date: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    sim_start_date: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    data: Mapped[dict] = mapped_column(JSON)
