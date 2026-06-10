from fastapi import APIRouter, Header, HTTPException

from app.schemas.auth import LoginReply, LoginRequest, UserListReply, UserProfile
from app.services.auth_service import (
    authenticate_user,
    build_demo_token,
    list_demo_users,
    user_from_token,
)


router = APIRouter()


@router.post("/login", response_model=LoginReply)
def login(payload: LoginRequest):
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"access_token": build_demo_token(user["user_id"]), "user": user}


@router.get("/me", response_model=UserProfile)
def me(authorization: str = Header(default="")):
    token = authorization.removeprefix("Bearer ").strip()
    user = user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or missing demo token")
    return user


@router.get("/users", response_model=UserListReply)
def users():
    return {"items": list_demo_users()}
