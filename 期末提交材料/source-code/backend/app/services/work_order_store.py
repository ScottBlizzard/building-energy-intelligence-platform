from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from app.core.config import get_settings


_STATUS_ORDER = {"处理中": 0, "已忽略": 1, "已完成": 2}
_PRIORITY_ORDER = {"高": 0, "中": 1, "低": 2}


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


def _sort_orders(items: List[Dict]) -> List[Dict]:
    return sorted(
        items,
        key=lambda item: (
            _STATUS_ORDER.get(item.get("status"), 9),
            _PRIORITY_ORDER.get(item.get("priority"), 9),
            item.get("created_at", ""),
        ),
    )


def list_work_orders() -> List[Dict]:
    return _sort_orders(_read_orders())


def create_work_order(payload: Dict) -> Dict:
    orders = _read_orders()
    source_record_id = payload.get("source_record_id")
    if source_record_id:
        for item in orders:
            if item.get("source_record_id") == source_record_id and item.get("status") != "已完成":
                item.update({key: value for key, value in payload.items() if value not in (None, "")})
                item["updated_at"] = _now()
                _write_orders(orders)
                return item

    created_at = _now()
    order = {
        **payload,
        "work_order_id": payload.get("work_order_id") or f"WO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "status": payload.get("status") or "处理中",
        "note": payload.get("note") or "",
        "created_at": created_at,
        "updated_at": created_at,
    }
    orders.append(order)
    _write_orders(orders)
    return order


def update_work_order(
    work_order_id: str,
    *,
    status: Optional[str] = None,
    note: Optional[str] = None,
    owner_role: Optional[str] = None,
) -> Optional[Dict]:
    orders = _read_orders()
    for item in orders:
        if item.get("work_order_id") == work_order_id:
            if status is not None:
                item["status"] = status
            if note is not None:
                item["note"] = note
            if owner_role is not None:
                item["owner_role"] = owner_role
            item["updated_at"] = _now()
            _write_orders(orders)
            return item
    return None
