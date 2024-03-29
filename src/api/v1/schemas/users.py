from datetime import datetime

from typing import Optional, List
from pydantic import BaseModel

__all__ = (
    "UserModel",
    "UserCreate",
    "UserCreated",
    "UserListResponse",
    "UserAuth",
    "Tokens",
    "Message",
    "EditProfileResult"
)


class UserCreated(BaseModel):
    username: str
    email:str


class UserAuth(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserModel(BaseModel):
    id: Optional[int]
    username: str
    roles: List[str] = ['common user']
    created_at: datetime
    uuid:  str
    is_totp_enabled: bool = False
    is_active: bool = True
    email: str


class UserListResponse(BaseModel):
    users: list[UserModel] = []


class Tokens(BaseModel):
    access_token: str
    refresh_token: str


class TokenPayload(BaseModel):
    exp: datetime
    iat: datetime
    scope: str
    sub: str


class Message(BaseModel):
    msg: str


class EditProfileResult(BaseModel):
    msg: str
    user: UserModel
    access_token: str