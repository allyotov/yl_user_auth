from datetime import datetime

from pydantic import BaseModel

__all__ = (
    "UserModel",
    "UserCreate",
    "UserListResponse",
)


class UserBase(BaseModel):
    title: str
    description: str


class UserCreate(UserBase):
    ...


class UserModel(UserBase):
    id: int
    created_at: datetime


class UserListResponse(BaseModel):
    users: list[UserModel] = []