from datetime import datetime

from typing import Optional, List
from pydantic import BaseModel

__all__ = (
    "UserModel",
    "UserCreate",
    "UserCreated",
    "UserListResponse",
)


class UserCreated(BaseModel):
    username: str
    email:str


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


# class User(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     username: str = Field(nullable=False)
#     roles: List[str] = Field(default=[])
#     created_at: datetime = Field(default=datetime.utcnow(), nullable=False)
#     uuid:  str = Field()
#     is_totp_enabled: bool = Field(default=False)
#     is_active: bool = Field(default=True)
#     email: str = Field(nullable=False)