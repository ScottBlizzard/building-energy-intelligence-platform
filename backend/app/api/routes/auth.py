from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import current_user_from_header
from app.schemas.auth import LoginReply, LoginRequest, UserListReply, UserProfile
from app.services.auth_service import (
    authenticate_user,
    build_demo_token,
    list_demo_users,
)


router = APIRouter()


@router.post("/login", response_model=LoginReply)
def login(payload: LoginRequest):
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"access_token": build_demo_token(user["user_id"]), "user": user}


@router.get("/me", response_model=UserProfile)
def me(user=Depends(current_user_from_header)):
    return user


@router.get("/users", response_model=UserListReply)
def users():
    return {"items": list_demo_users()}
