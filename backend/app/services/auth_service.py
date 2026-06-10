from __future__ import annotations

from typing import Dict, List, Optional


DEMO_USERS: Dict[str, Dict] = {
    "admin": {
        "user_id": "admin",
        "username": "admin",
        "password": "admin123",
        "display_name": "能源运营管理员",
        "role": "admin",
        "specialty": "全局调度",
        "enabled": True,
    },
    "worker_ahu": {
        "user_id": "worker_ahu",
        "username": "worker_ahu",
        "password": "worker123",
        "display_name": "空调机组巡检员",
        "role": "worker",
        "specialty": "AHU",
        "enabled": True,
    },
    "worker_chiller": {
        "user_id": "worker_chiller",
        "username": "worker_chiller",
        "password": "worker123",
        "display_name": "制冷机房值班员",
        "role": "worker",
        "specialty": "CH",
        "enabled": True,
    },
}


def _public_user(user: Dict) -> Dict:
    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "display_name": user["display_name"],
        "role": user["role"],
        "specialty": user.get("specialty", ""),
        "enabled": bool(user.get("enabled", True)),
    }


def list_demo_users() -> List[Dict]:
    return [_public_user(user) for user in DEMO_USERS.values()]


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    user = DEMO_USERS.get(username)
    if not user or not user.get("enabled", True):
        return None
    if user.get("password") != password:
        return None
    return _public_user(user)


def build_demo_token(user_id: str) -> str:
    return f"demo-token:{user_id}"


def user_from_token(token: str) -> Optional[Dict]:
    prefix = "demo-token:"
    if not token.startswith(prefix):
        return None
    user = DEMO_USERS.get(token[len(prefix) :])
    if not user:
        return None
    return _public_user(user)


def get_user(user_id: Optional[str]) -> Optional[Dict]:
    if not user_id:
        return None
    user = DEMO_USERS.get(user_id)
    if not user:
        return None
    return _public_user(user)


def resolve_worker_for_equipment(equipment_id: str = "", equipment_type: str = "") -> Dict:
    text = f"{equipment_id} {equipment_type}".upper()
    if "CH" in text or "CT" in text or "冷水" in equipment_type or "冷却" in equipment_type:
        return _public_user(DEMO_USERS["worker_chiller"])
    return _public_user(DEMO_USERS["worker_ahu"])
