from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from app.core.config import get_settings
from app.services.auth_service import get_user, resolve_worker_for_equipment


LEGACY_STATUS_MAP = {
    "处理中": "in_progress",
    "已完成": "closed",
    "已忽略": "ignored",
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

# Estimated post-repair recovery factors. There is no measured "after" reading in
# the sample dataset, so these are used to project an estimated improvement from the
# captured baseline. Outputs carry `after_is_estimated=True` and are labelled as
# estimates in the UI/report, never presented as measured values.
ESTIMATED_KWH_RECOVERY_FACTOR = 0.78
ESTIMATED_COP_RECOVERY_FACTOR = 1.15


def _store_path() -> Path:
    return get_settings().work_order_file


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _read_orders() -> List[Dict]:
    path = _store_path()
    if not path.exists():
        return []

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    return payload if isinstance(payload, list) else []


def _write_orders(items: List[Dict]) -> None:
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
        "event_id": f"TL-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
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
        "work_order_id": payload.get("work_order_id") or f"WO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "status": status,
        "status_label": _status_label(status),
        "assignee_id": assignee_id,
        "assignee_name": assignee_name,
        "created_by": payload.get("created_by") or "admin",
        "reviewed_by": "",
        "note": payload.get("note") or "",
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


def create_work_order_from_anomaly(payload: Dict, operator_id: str = "admin") -> Dict:
    assignee = get_user(payload.get("assignee_id")) if payload.get("assignee_id") else None
    if not assignee:
        assignee = resolve_worker_for_equipment(
            payload.get("equipment_id", ""), payload.get("equipment_type", "")
        )
        payload["assignee_id"] = assignee["user_id"]
        payload["assignee_name"] = assignee["display_name"]

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
    if new_status == "closed":
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
