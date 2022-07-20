from datetime import datetime
from email.policy import default
from typing import Optional, List
from sqlalchemy import null

from sqlmodel import Field, SQLModel

__all__ = ("User",)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(nullable=False)
    roles: List[str] = Field(default=['common_user'])
    created_at: datetime = Field(default=datetime.utcnow(), nullable=False)
    uuid:  str = Field()
    is_totp_enabled: bool = Field(default=False)
    is_active: bool = Field(default=True)
    email: str = Field(nullable=False)
    password: str = Field(nullable=False)