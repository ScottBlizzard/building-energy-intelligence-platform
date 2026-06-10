from typing import List

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class UserProfile(BaseModel):
    user_id: str
    username: str
    display_name: str
    role: str
    specialty: str = ""
    enabled: bool = True


class LoginReply(BaseModel):
    access_token: str
    token_type: str = "demo"
    user: UserProfile


class UserListReply(BaseModel):
    items: List[UserProfile]
