from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from app.core.config import get_settings
from app.services import simulation_service
from app.services.auth_service import get_user, resolve_worker_for_equipment


LEGACY_STATUS_MAP = {
    "处理中": "in_progress",
    "已完成": "closed",
    "已忽略": "ignored",
    "待分派": "pending_confirm",
    "待验证": "pending_review",
    "已关闭": "closed",
}

STATUS_LABELS = {
    "pending_confirm": "待确认",
    "assigned": "已派单",
    "in_progress": "处理中",
    "pending_review": "待复核",
    "rejected": "已驳回",
    "closed": "已关闭",
    "ignored": "已忽略",
}

STATUS_ORDER = {
    "pending_confirm": 0,
    "assigned": 1,
    "in_progress": 2,
    "rejected": 3,
    "pending_review": 4,
    "closed": 5,
    "ignored": 6,
}

PRIORITY_ORDER = {"高": 0, "中": 1, "低": 2}
_CLOSED_STATUSES = {"closed", "ignored", "已关闭", "已完成", "已忽略"}
# 工人“占用”状态：手上有已派/处理中工单即视为忙碌、被锁定，不能再接第二单。
# 提交复核(pending_review)后视为完工、转回空闲，可承接下一单。
_ACTIVE_STATUSES = {"assigned", "in_progress"}


class WorkerBusyError(Exception):
    """Raised when assigning a new active order to an already-busy worker."""


def _active_order_for_worker(
    orders: List[Dict],
    assignee_id: str,
    *,
    exclude_work_order_id: Optional[str] = None,
    exclude_record_id: Optional[str] = None,
) -> Optional[Dict]:
    """Return the worker's current active (assigned/in_progress) order, if any.

    Used to enforce the busy-lock: a worker may only hold one active order at a
    time. The order currently being created/assigned is excluded so re-saving
    the same order is not treated as a conflict.
    """
    if not assignee_id:
        return None
    for order in orders:
        if order.get("assignee_id") != assignee_id:
            continue
        if _canonical_status(order.get("status")) not in _ACTIVE_STATUSES:
            continue
        if exclude_work_order_id and order.get("work_order_id") == exclude_work_order_id:
            continue
        if exclude_record_id and order.get("source_record_id") == exclude_record_id:
            continue
        return order
    return None

# Estimated post-repair recovery factors. There is no measured "after" reading in
# the sample dataset, so these are used to project an estimated improvement from the
# captured baseline. Outputs carry `after_is_estimated=True` and are labelled as
# estimates in the UI/report, never presented as measured values.
ESTIMATED_KWH_RECOVERY_FACTOR = 0.78
ESTIMATED_COP_RECOVERY_FACTOR = 1.15


def _store_path() -> Path:
    return get_settings().work_order_file


def _now() -> str:
    # Follow the sandbox clock so created/closed/timeline times stay on the
    # simulated date during a demo (falls back to real time when inactive).
    return simulation_service.now_str()


def _now_dt() -> datetime:
    return simulation_service.now()


def _read_orders() -> List[Dict]:
    from app.db import repository as db_repo

    if db_repo.is_enabled():
        return db_repo.read_work_orders()

    path = _store_path()
    if not path.exists():
        return []

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    return payload if isinstance(payload, list) else []


def _write_orders(items: List[Dict]) -> None:
    from app.db import repository as db_repo

    if db_repo.is_enabled():
        db_repo.write_work_orders(items)
        return

    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(".tmp")
    temp_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(path)


def _canonical_status(status: Optional[str], default: str = "pending_confirm") -> str:
    if not status:
        return default
    return LEGACY_STATUS_MAP.get(status, status)


def _status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)


def _operator(operator_id: Optional[str]) -> Dict:
    user = get_user(operator_id) or get_user("admin")
    return user or {"user_id": "system", "display_name": "系统", "role": "system"}


def _timeline_event(
    *,
    action: str,
    from_status: Optional[str],
    to_status: str,
    operator_id: Optional[str],
    note: str = "",
) -> Dict:
    operator = _operator(operator_id)
    created_at = _now()
    return {
        "event_id": f"TL-{_now_dt().strftime('%Y%m%d%H%M%S%f')}",
        "action": action,
        "from_status": from_status,
        "from_status_label": _status_label(from_status or ""),
        "to_status": to_status,
        "to_status_label": _status_label(to_status),
        "operator_id": operator["user_id"],
        "operator_name": operator["display_name"],
        "operator_role": operator["role"],
        "note": note,
        "created_at": created_at,
    }


def _normalize_order(item: Dict) -> Dict:
    normalized = dict(item)
    canonical_status = _canonical_status(normalized.get("status"))
    normalized["status"] = canonical_status
    normalized["status_label"] = _status_label(canonical_status)
    normalized["note"] = normalized.get("note") or ""
    normalized["timeline"] = normalized.get("timeline") or []
    normalized["assignee_id"] = normalized.get("assignee_id") or ""
    normalized["assignee_name"] = normalized.get("assignee_name") or ""
    normalized["created_by"] = normalized.get("created_by") or "admin"
    normalized["reviewed_by"] = normalized.get("reviewed_by") or ""
    normalized["actual_cause"] = normalized.get("actual_cause") or ""
    normalized["resolution_note"] = normalized.get("resolution_note") or ""
    normalized["parts_used"] = normalized.get("parts_used") or ""
    normalized["safety_note"] = normalized.get("safety_note") or ""
    normalized["review_note"] = normalized.get("review_note") or ""
    normalized["attachment_name"] = normalized.get("attachment_name") or ""
    normalized["attachment_note"] = normalized.get("attachment_note") or ""
    normalized["attachment_data"] = normalized.get("attachment_data") or ""
    normalized["recovery_confirmed"] = bool(normalized.get("recovery_confirmed", False))
    normalized["before_kwh"] = normalized.get("before_kwh")
    normalized["before_cop"] = normalized.get("before_cop")
    normalized["after_kwh"] = normalized.get("after_kwh")
    normalized["after_cop"] = normalized.get("after_cop")
    normalized["after_is_estimated"] = bool(normalized.get("after_is_estimated", False))
    return normalized


def _sort_orders(items: List[Dict]) -> List[Dict]:
    normalized = [_normalize_order(item) for item in items]
    return sorted(
        normalized,
        key=lambda item: (
            STATUS_ORDER.get(item.get("status"), 9),
            PRIORITY_ORDER.get(item.get("priority"), 9),
            item.get("created_at", ""),
        ),
    )


def _find_order(orders: List[Dict], work_order_id: str) -> Optional[Dict]:
    for item in orders:
        if item.get("work_order_id") == work_order_id:
            return item
    return None


def _open_status(status: str) -> bool:
    return _canonical_status(status) not in {"closed", "ignored"}


def list_work_orders(
    *,
    assignee_id: Optional[str] = None,
    status: Optional[str] = None,
    role: Optional[str] = None,
) -> List[Dict]:
    items = _sort_orders(_read_orders())
    if assignee_id:
        items = [item for item in items if item.get("assignee_id") == assignee_id]
    if status:
        canonical = _canonical_status(status)
        items = [item for item in items if item.get("status") == canonical]
    if role == "worker" and assignee_id:
        items = [item for item in items if item.get("assignee_id") == assignee_id]
    return items


def create_work_order(payload: Dict) -> Dict:
    orders = _read_orders()
    source_record_id = payload.get("source_record_id")
    default_status = "assigned" if payload.get("assignee_id") else "pending_confirm"

    if source_record_id:
        for item in orders:
            if item.get("source_record_id") == source_record_id and _open_status(item.get("status", "")):
                item.update({key: value for key, value in payload.items() if value not in (None, "")})
                item["status"] = _canonical_status(item.get("status"), default_status)
                item["verification_status"] = item.get("verification_status") or "未验证"
                item["updated_at"] = _now()
                item["status_label"] = _status_label(item["status"])
                _write_orders(orders)
                return _normalize_order(item)

    created_at = _now()
    status = _canonical_status(payload.get("status"), default_status)
    assignee_id = payload.get("assignee_id") or ""
    assignee_name = payload.get("assignee_name") or ""
    if assignee_id and not assignee_name:
        assignee = get_user(assignee_id)
        assignee_name = assignee["display_name"] if assignee else assignee_id

    order = {
        **payload,
        "work_order_id": payload.get("work_order_id") or f"WO-{_now_dt().strftime('%Y%m%d%H%M%S')}",
        "status": status,
        "status_label": _status_label(status),
        "assignee_id": assignee_id,
        "assignee_name": assignee_name,
        "created_by": payload.get("created_by") or "admin",
        "reviewed_by": "",
        "note": payload.get("note") or "",
        "verification_status": payload.get("verification_status") or "未验证",
        "dispatch_action": payload.get("dispatch_action") or "",
        "resolution_action": payload.get("resolution_action") or "",
        "verification_result": payload.get("verification_result") or "",
        "actual_cause": payload.get("actual_cause") or "",
        "resolution_note": payload.get("resolution_note") or "",
        "review_note": payload.get("review_note") or "",
        "parts_used": payload.get("parts_used") or "",
        "safety_note": payload.get("safety_note") or "",
        "attachment_name": payload.get("attachment_name") or "",
        "attachment_note": payload.get("attachment_note") or "",
        "recovery_confirmed": bool(payload.get("recovery_confirmed", False)),
        "closed_at": payload.get("closed_at") or "",
        "before_kwh": payload.get("before_kwh"),
        "before_cop": payload.get("before_cop"),
        "created_at": created_at,
        "updated_at": created_at,
        "timeline": [
            _timeline_event(
                action="create",
                from_status=None,
                to_status=status,
                operator_id=payload.get("created_by") or "admin",
                note=payload.get("note") or "由异常记录生成工单",
            )
        ],
    }
    orders.append(order)
    _write_orders(orders)
    return _normalize_order(order)


def clear_work_orders() -> int:
    """Remove every persisted work order. Returns how many were cleared.

    Used by the demo reset so a rehearsal can start from a clean slate.
    """
    count = len(_read_orders())
    _write_orders([])
    return count


def _reference_seed_payloads() -> List[Dict]:
    """A small set of historical CLOSED work orders used to seed a demo.

    They give the worker workbench's "similar cases" and the operation report
    realistic prior content instead of an empty list on the very first close.
    """
    return [
        {
            "work_order_id": "WO-SEED-AHU-001",
            "source_record_id": "SEED-AHU-001",
            "priority": "中",
            "status": "closed",
            "building_id": "BLD-A",
            "building_name": "综合教学楼A",
            "floor_label": "3F",
            "zone_name": "3F",
            "equipment_id": "AHU-A-3F-04",
            "equipment_type": "空气处理机组",
            "timestamp": "2026-04-12 10:00:00",
            "anomaly_reason": "电耗高于同时段基线",
            "possible_cause": "新风阀卡滞导致风量偏大",
            "recommended_action": "复位风阀并校准新风比例",
            "owner_role": "worker",
            "assignee_id": "worker_ahu",
            "assignee_name": "空调机组巡检员",
            "created_by": "admin",
            "reviewed_by": "admin",
            "actual_cause": "新风阀执行器卡滞，新风过量",
            "resolution_note": "更换执行器并校准新风比例，电耗回落至基线",
            "before_kwh": 320.0,
            "after_kwh": 249.6,
            "after_is_estimated": True,
            "recovery_confirmed": True,
            "estimated_saving_yuan": 57.7,
            "wasted_cost_yuan": 73.9,
            "carbon_kg": 51.4,
            "risk_score": 62,
            "sla_hours": 24,
            "review_note": "现场处理到位，准予关闭",
            "closed_at": "2026-04-12 15:30:00",
            "created_at": "2026-04-12 09:50:00",
            "updated_at": "2026-04-12 15:30:00",
        },
        {
            "work_order_id": "WO-SEED-FCU-002",
            "source_record_id": "SEED-FCU-002",
            "priority": "低",
            "status": "closed",
            "building_id": "BLD-C",
            "building_name": "图书信息楼C",
            "floor_label": "2F",
            "zone_name": "2F",
            "equipment_id": "FCU-C-2F-04",
            "equipment_type": "风机盘管",
            "timestamp": "2026-04-18 14:00:00",
            "anomaly_reason": "电耗高于同时段基线",
            "possible_cause": "盘管滤网堵塞、末端温控失准",
            "recommended_action": "清洗滤网并校准末端温控器",
            "owner_role": "worker",
            "assignee_id": "worker_ahu",
            "assignee_name": "空调机组巡检员",
            "created_by": "admin",
            "reviewed_by": "admin",
            "actual_cause": "盘管滤网堵塞导致风机长时间高速运行",
            "resolution_note": "清洗滤网、复位温控设定，运行电耗恢复",
            "before_kwh": 180.0,
            "after_kwh": 140.4,
            "after_is_estimated": True,
            "recovery_confirmed": True,
            "estimated_saving_yuan": 32.5,
            "wasted_cost_yuan": 41.0,
            "carbon_kg": 28.6,
            "risk_score": 41,
            "sla_hours": 48,
            "review_note": "已恢复，关闭归档",
            "closed_at": "2026-04-18 17:10:00",
            "created_at": "2026-04-18 13:40:00",
            "updated_at": "2026-04-18 17:10:00",
        },
        {
            "work_order_id": "WO-SEED-CH-003",
            "source_record_id": "SEED-CH-003",
            "priority": "高",
            "status": "closed",
            "building_id": "BLD-C",
            "building_name": "图书信息楼C",
            "floor_label": "B1",
            "zone_name": "B1",
            "equipment_id": "CH-C-B1-04",
            "equipment_type": "冷水机组",
            "timestamp": "2026-04-25 09:00:00",
            "anomaly_reason": "COP 低于健康阈值",
            "possible_cause": "冷凝器换热效率下降、冷却水温偏高",
            "recommended_action": "清洗冷凝器并核对冷却塔联动",
            "owner_role": "worker",
            "assignee_id": "worker_chiller",
            "assignee_name": "制冷机房值班员",
            "created_by": "admin",
            "reviewed_by": "admin",
            "actual_cause": "冷凝器结垢导致换热效率下降，COP 偏低",
            "resolution_note": "化学清洗冷凝器并调整冷却塔出水温度，COP 回升",
            "before_kwh": 540.0,
            "after_kwh": 421.2,
            "before_cop": 2.1,
            "after_cop": 2.4,
            "after_is_estimated": True,
            "recovery_confirmed": True,
            "estimated_saving_yuan": 97.4,
            "wasted_cost_yuan": 121.8,
            "carbon_kg": 84.8,
            "risk_score": 78,
            "sla_hours": 12,
            "review_note": "COP 恢复，准予关闭",
            "closed_at": "2026-04-25 16:00:00",
            "created_at": "2026-04-25 08:30:00",
            "updated_at": "2026-04-25 16:00:00",
        },
    ]


def seed_reference_orders() -> int:
    """Add historical closed reference orders if they are not present yet.

    Idempotent by ``work_order_id``; returns how many new seeds were added.
    """
    seeds = _reference_seed_payloads()
    orders = _read_orders()
    existing_ids = {item.get("work_order_id") for item in orders}
    added = 0
    for seed in seeds:
        if seed["work_order_id"] in existing_ids:
            continue
        seed = dict(seed)
        seed["timeline"] = [
            _timeline_event(
                action="create",
                from_status=None,
                to_status="assigned",
                operator_id="admin",
                note="历史样例工单（演示种子）",
            ),
            _timeline_event(
                action="review_approve",
                from_status="pending_review",
                to_status="closed",
                operator_id="admin",
                note=seed.get("review_note") or "复核通过，工单关闭",
            ),
        ]
        orders.append(seed)
        added += 1
    if added:
        _write_orders(orders)
    return added


def create_work_order_from_anomaly(payload: Dict, operator_id: str = "admin") -> Dict:
    assignee = get_user(payload.get("assignee_id")) if payload.get("assignee_id") else None
    if not assignee:
        assignee = resolve_worker_for_equipment(
            payload.get("equipment_id", ""), payload.get("equipment_type", "")
        )
        payload["assignee_id"] = assignee["user_id"]
        payload["assignee_name"] = assignee["display_name"]

    # 忙碌锁定：该对口工人若已有处理中的工单，则不能再派第二单。
    busy = _active_order_for_worker(
        _read_orders(),
        payload.get("assignee_id", ""),
        exclude_record_id=payload.get("source_record_id"),
    )
    if busy:
        raise WorkerBusyError(
            f"{assignee['display_name']}当前正在处理工单 {busy.get('work_order_id')}"
            f"（{busy.get('equipment_id')}），完工后才能再派单。"
        )

    payload["created_by"] = operator_id
    payload["status"] = "assigned"
    payload["note"] = payload.get("note") or f"管理员已派单给{payload['assignee_name']}"
    return create_work_order(payload)


def update_work_order(
    work_order_id: str,
    *,
    status: Optional[str] = None,
    note: Optional[str] = None,
    owner_role: Optional[str] = None,
    dispatch_action: Optional[str] = None,
    resolution_action: Optional[str] = None,
    verification_result: Optional[str] = None,
    verification_status: Optional[str] = None,
) -> Optional[Dict]:
    orders = _read_orders()
    item = _find_order(orders, work_order_id)
    if not item:
        return None

    old_status = _canonical_status(item.get("status"))
    new_status = _canonical_status(status, old_status) if status is not None else old_status
    item["status"] = new_status
    item["status_label"] = _status_label(new_status)
    if note is not None:
        item["note"] = note
    if owner_role is not None:
        item["owner_role"] = owner_role
    if dispatch_action is not None:
        item["dispatch_action"] = dispatch_action
    if resolution_action is not None:
        item["resolution_action"] = resolution_action
    if verification_result is not None:
        item["verification_result"] = verification_result
    if verification_status is not None:
        item["verification_status"] = verification_status
    if new_status == "in_progress":
        item["dispatched_at"] = item.get("dispatched_at") or _now()
    if new_status == "pending_review":
        item["verification_status"] = verification_status or item.get("verification_status") or "待验证"
        item["verification_requested_at"] = item.get("verification_requested_at") or _now()
    if new_status == "closed":
        item["verification_status"] = verification_status or "通过"
        item["verified_at"] = item.get("verified_at") or _now()
        item["closed_at"] = item.get("closed_at") or _now()
    item.setdefault("timeline", []).append(
        _timeline_event(
            action="update",
            from_status=old_status,
            to_status=new_status,
            operator_id="admin",
            note=note or "兼容接口更新工单",
        )
    )
    item["updated_at"] = _now()
    _write_orders(orders)
    return _normalize_order(item)


def assign_work_order(work_order_id: str, assignee_id: str, operator_id: str = "admin", note: str = "") -> Optional[Dict]:
    orders = _read_orders()
    item = _find_order(orders, work_order_id)
    assignee = get_user(assignee_id)
    if not item or not assignee or assignee["role"] != "worker":
        return None

    # 忙碌锁定：目标工人若已有处理中的其他工单，则不能再派给他。
    busy = _active_order_for_worker(
        orders, assignee["user_id"], exclude_work_order_id=work_order_id
    )
    if busy:
        raise WorkerBusyError(
            f"{assignee['display_name']}当前正在处理工单 {busy.get('work_order_id')}"
            f"（{busy.get('equipment_id')}），完工后才能再派单。"
        )

    old_status = _canonical_status(item.get("status"))
    item["status"] = "assigned"
    item["status_label"] = _status_label("assigned")
    item["assignee_id"] = assignee["user_id"]
    item["assignee_name"] = assignee["display_name"]
    item["note"] = note or item.get("note", "")
    item.setdefault("timeline", []).append(
        _timeline_event(
            action="assign",
            from_status=old_status,
            to_status="assigned",
            operator_id=operator_id,
            note=note or f"派单给{assignee['display_name']}",
        )
    )
    item["updated_at"] = _now()
    _write_orders(orders)
    return _normalize_order(item)


def accept_work_order(work_order_id: str, operator_id: str, note: str = "") -> Optional[Dict]:
    orders = _read_orders()
    item = _find_order(orders, work_order_id)
    if not item or item.get("assignee_id") != operator_id:
        return None

    old_status = _canonical_status(item.get("status"))
    if old_status not in {"assigned", "rejected"}:
        return None

    item["status"] = "in_progress"
    item["status_label"] = _status_label("in_progress")
    item.setdefault("timeline", []).append(
        _timeline_event(
            action="accept",
            from_status=old_status,
            to_status="in_progress",
            operator_id=operator_id,
            note=note or "运维工人已接单",
        )
    )
    item["updated_at"] = _now()
    _write_orders(orders)
    return _normalize_order(item)


def submit_work_order(
    work_order_id: str,
    *,
    operator_id: str,
    actual_cause: str,
    resolution_note: str,
    recovery_confirmed: bool,
    parts_used: str = "",
    safety_note: str = "",
    attachment_name: str = "",
    attachment_note: str = "",
    attachment_data: str = "",
) -> Optional[Dict]:
    orders = _read_orders()
    item = _find_order(orders, work_order_id)
    if not item or item.get("assignee_id") != operator_id:
        return None

    old_status = _canonical_status(item.get("status"))
    if old_status not in {"in_progress", "rejected"}:
        return None

    item["status"] = "pending_review"
    item["status_label"] = _status_label("pending_review")
    item["actual_cause"] = actual_cause
    item["resolution_note"] = resolution_note
    item["recovery_confirmed"] = recovery_confirmed
    item["parts_used"] = parts_used
    item["safety_note"] = safety_note
    item["attachment_name"] = attachment_name
    item["attachment_note"] = attachment_note
    if attachment_data:
        item["attachment_data"] = attachment_data
    # ---- estimated before / after comparison ----
    # No post-repair measurement exists in the dataset, so the "after" values are
    # projected estimates derived from the captured baseline (real "before") using
    # conservative recovery factors. They are surfaced to the UI as estimates only.
    before_kwh = item.get("before_kwh")
    before_cop = item.get("before_cop")
    if recovery_confirmed and before_kwh:
        item["after_kwh"] = round(before_kwh * ESTIMATED_KWH_RECOVERY_FACTOR, 2)
    else:
        item["after_kwh"] = round(before_kwh, 2) if before_kwh else None
    if recovery_confirmed and before_cop:
        item["after_cop"] = round(before_cop * ESTIMATED_COP_RECOVERY_FACTOR, 2)
    else:
        item["after_cop"] = round(before_cop, 2) if before_cop else None
    item["after_is_estimated"] = bool(recovery_confirmed and (before_kwh or before_cop))
    item.setdefault("timeline", []).append(
        _timeline_event(
            action="submit",
            from_status=old_status,
            to_status="pending_review",
            operator_id=operator_id,
            note=resolution_note,
        )
    )
    item["updated_at"] = _now()
    _write_orders(orders)
    return _normalize_order(item)


def review_work_order(
    work_order_id: str,
    *,
    operator_id: str = "admin",
    approved: bool,
    review_note: str = "",
) -> Optional[Dict]:
    orders = _read_orders()
    item = _find_order(orders, work_order_id)
    if not item:
        return None

    old_status = _canonical_status(item.get("status"))
    if old_status != "pending_review":
        return None

    new_status = "closed" if approved else "rejected"
    item["status"] = new_status
    item["status_label"] = _status_label(new_status)
    item["reviewed_by"] = operator_id
    item["review_note"] = review_note
    if approved:
        item["closed_at"] = _now()
        # Causal link: from the (simulated) repair date onward the equipment
        # recovers to its normal baseline in the revealed future.
        from app.services import simulation_service

        equipment_id = item.get("equipment_id")
        if equipment_id:
            simulation_service.register_intervention(equipment_id)
    item.setdefault("timeline", []).append(
        _timeline_event(
            action="review_approve" if approved else "review_reject",
            from_status=old_status,
            to_status=new_status,
            operator_id=operator_id,
            note=review_note or ("复核通过，工单关闭" if approved else "复核不通过，退回处理"),
        )
    )
    item["updated_at"] = _now()
    _write_orders(orders)
    return _normalize_order(item)


def ignore_work_order(work_order_id: str, operator_id: str = "admin", note: str = "") -> Optional[Dict]:
    orders = _read_orders()
    item = _find_order(orders, work_order_id)
    if not item:
        return None

    old_status = _canonical_status(item.get("status"))
    item["status"] = "ignored"
    item["status_label"] = _status_label("ignored")
    item["reviewed_by"] = operator_id
    item["note"] = note or item.get("note", "")
    item.setdefault("timeline", []).append(
        _timeline_event(
            action="ignore",
            from_status=old_status,
            to_status="ignored",
            operator_id=operator_id,
            note=note or "管理员判断无需派单处理",
        )
    )
    item["updated_at"] = _now()
    _write_orders(orders)
    return _normalize_order(item)


def build_work_order_metrics(items: Optional[List[Dict]] = None) -> Dict:
    orders = _sort_orders(items if items is not None else _read_orders())
    counts = {status: 0 for status in STATUS_LABELS}
    for item in orders:
        counts[item["status"]] = counts.get(item["status"], 0) + 1

    open_orders = [item for item in orders if item["status"] not in {"closed", "ignored"}]
    closed_orders = [item for item in orders if item["status"] == "closed"]
    pending_review = [item for item in orders if item["status"] == "pending_review"]
    high_priority_open = [
        item for item in open_orders if item.get("priority") == "高"
    ]

    assigned_count = len([item for item in orders if item["status"] == "assigned"])
    newly_assigned = max(0, assigned_count)

    return {
        "total": len(orders),
        "open_count": len(open_orders),
        "closed_count": len(closed_orders),
        "pending_review_count": len(pending_review),
        "high_priority_open_count": len(high_priority_open),
        "newly_assigned": newly_assigned,
        "status_counts": counts,
        "status_labels": STATUS_LABELS,
        "next_actions": [
            "优先复核待复核工单",
            "处理高优先级未关闭工单",
            "确认待确认异常是否需要派单",
        ],
    }


def create_pending_confirm_drafts(anomaly_payloads: List[Dict], operator_id: str = "admin") -> Dict:
    """Batch create pending_confirm draft work orders from anomalies.
    Skips anomalies that already have an open work order."""
    orders = _read_orders()
    existing_ids = {
        item["source_record_id"]
        for item in orders
        if item.get("source_record_id") and _open_status(item.get("status", ""))
    }
    created = []
    skipped = 0
    for anomaly in anomaly_payloads:
        record_id = anomaly.get("source_record_id")
        if record_id and record_id in existing_ids:
            skipped += 1
            continue
        payload = {
            **anomaly,
            "status": "pending_confirm",
            "created_by": operator_id,
            "note": f"系统自动从异常记录生成，等待管理员确认。",
        }
        order = create_work_order(payload)
        created.append(order)
        if record_id:
            existing_ids.add(record_id)

    return {
        "created": created,
        "created_count": len(created),
        "skipped_count": skipped,
        "message": f"已生成 {len(created)} 个待确认工单，跳过 {skipped} 个已有工单的异常。",
    }
