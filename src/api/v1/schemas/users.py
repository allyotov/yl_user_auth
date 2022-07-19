from datetime import datetime

from typing import Optional, List
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
    username: str
    email: str
    password: str


class UserModel(UserBase):
    id: Optional[int]
    username: str
    roles: List[str]
    created_at: datetime
    uuid:  str
    is_totp_enabled: bool
    is_active: bool
    email: str


class UserListResponse(BaseModel):
    users: list[UserModel] = []


# class User(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     username: str = Field(nullable=False)
#     roles: List[str] = Field(default=[])
#     created_at: datetime = Field(default=datetime.utcnow(), nullable=False)
#     uuid:  str = Field()
#     is_totp_enabled: bool = Field(default=False)
#     is_active: bool = Field(default=True)
#     email: str = Field(nullable=False)