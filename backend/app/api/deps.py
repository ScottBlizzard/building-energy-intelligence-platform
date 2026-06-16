from __future__ import annotations

from typing import Dict, Optional

from fastapi import Header, HTTPException

from app.core.config import get_settings
from app.services.auth_service import get_user, user_from_token


def _token_from_authorization(authorization: str = "") -> str:
    if not authorization:
        return ""
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() == "bearer":
        return value.strip()
    return authorization.strip()


def current_user_from_header(authorization: str = Header(default="")) -> Dict:
    token = _token_from_authorization(authorization)
    user = user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or missing demo token")
    return user


def resolve_operator_user(
    operator_id: Optional[str] = None,
    authorization: str = "",
    fallback_user_id: Optional[str] = None,
) -> Dict:
    token = _token_from_authorization(authorization)
    if token:
        user = user_from_token(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid or missing demo token")
        if operator_id and operator_id != user["user_id"]:
            raise HTTPException(status_code=403, detail="Operator does not match token user")
        return user

    if get_settings().app_env == "production":
        raise HTTPException(status_code=401, detail="Invalid or missing demo token")

    user = get_user(operator_id or fallback_user_id or "")
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or missing demo operator")
    return user


def require_admin_user(
    operator_id: Optional[str] = None,
    authorization: str = "",
    action: str = "perform this operation",
) -> Dict:
    user = resolve_operator_user(operator_id=operator_id, authorization=authorization)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail=f"Only admins can {action}.")
    return user


def require_worker_user(
    operator_id: Optional[str] = None,
    authorization: str = "",
    action: str = "perform this operation",
) -> Dict:
    user = resolve_operator_user(operator_id=operator_id, authorization=authorization)
    if user.get("role") != "worker":
        raise HTTPException(status_code=403, detail=f"Only workers can {action}.")
    return user
