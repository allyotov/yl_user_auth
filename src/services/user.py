from cmath import log
import logging
import json
from functools import lru_cache
from os import access
from typing import Optional
import uuid

from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from sqlmodel import Session

from src.api.v1.schemas import UserCreate, UserModel
from src.db import AbstractCache, get_cache, get_session
from src.models import User
from src.services import ServiceMixin
from src.services.auth import Auth

__all__ = ("UserService", "get_user_service")
auth_handler = Auth()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class UserService(ServiceMixin):
    def signup(self, user_details: UserCreate) -> dict:
        if self.session.query(User).filter(User.username==user_details.username).all():
            raise HTTPException(status_code=409, detail='Account with such username already exists')
        if self.session.query(User).filter(User.email==user_details.email).all():
            raise HTTPException(status_code=409, detail='Account with such email already exists')
        try:
            hashed_password = auth_handler.encode_password(user_details.password)
            new_user = User(username=user_details.username, 
                        email=user_details.email, 
                        password=hashed_password,
                        uuid=str(uuid.uuid4()))
            logger.debug(new_user.roles)
            self.session.add(new_user)
            self.session.commit()
            self.session.refresh(new_user)
            return new_user.dict()
        except:
            raise HTTPException(status_code=500, detail='Can\'t add user to database.')

    def login(self, user_details: UserCreate) -> dict:
        user = self.session.query(User).filter(User.username==user_details.username).one_or_none()
        if user is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Incorrect email')

        if not auth_handler.verify_password(user_details.password, user.password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Incorrect password')

        access_token = auth_handler.encode_token(user.username)
        refresh_token = auth_handler.encode_refresh_token(user.username)

        return {'access_token': access_token, 'refresh_token': refresh_token}

    def get_user_list(self) -> dict:
        """Получить список пользователей."""
        users = self.session.query(User).order_by(User.created_at).all()
        return {"user": [UserModel(**user.dict()) for user in users]}

    def get_user_detail(self, item_id: int) -> Optional[dict]:
        """Получить детальную информацию пользователя."""
        if cached_user := self.cache.get(key=f"user{item_id}"):
            return json.loads(cached_user)
        user = self.session.query(User).filter(User.id == item_id).first()
        if user:
            self.cache.set(key=f"user{user.id}", value=user.json())
        return user.dict() if user else None

    def create_user(self, user: UserCreate) -> dict:
        """Создать пользователя."""

        # check if user is already in db
        new_user = User(title=user.username, description=user.email, password=user.password)
        self.session.add(new_user)
        self.session.commit()
        self.session.refresh(new_user)
        return new_user.dict()


# get_user_service — это провайдер UserService. Синглтон
@lru_cache()
def get_user_service(
    cache: AbstractCache = Depends(get_cache),
    session: Session = Depends(get_session),
) -> UserService:
    return UserService(cache=cache, session=session)
