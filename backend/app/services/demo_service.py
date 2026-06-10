"""One-click demo reset so a rehearsal can return to its initial state.

Clears runtime work orders, budgets and the simulation clock, then re-seeds a
few historical closed reference work orders (for "similar cases" and report
content). Exposed via ``POST /api/v1/demo/reset`` and a button in the UI.
"""
from __future__ import annotations

from typing import Dict

from app.services import simulation_service
from app.services.budget_service import clear_budgets
from app.services.work_order_store import clear_work_orders, seed_reference_orders


def reset_demo(seed: bool = True) -> Dict:
    simulation_service.reset()
    cleared_orders = clear_work_orders()
    cleared_budgets = clear_budgets()
    seeded = seed_reference_orders() if seed else 0
    return {
        "reset": True,
        "cleared_work_orders": cleared_orders,
        "cleared_budgets": cleared_budgets,
        "seeded_reference_orders": seeded,
        "simulation": simulation_service.get_state(),
        "message": (
            f"演示已回到初始状态：清空 {cleared_orders} 个工单、{cleared_budgets} 条预算，"
            f"重置时间机器，并预置 {seeded} 条历史样例工单。"
        ),
    }
