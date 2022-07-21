import json
import logging
from functools import lru_cache
from typing import Optional, Any, Union, Tuple
import uuid

from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from pydantic import ValidationError
from sqlmodel import Session

from src.api.v1.schemas import UserCreate, UserModel
from src.api.v1.schemas.users import TokenPayload, Tokens
from src.db import AbstractCache, get_cache, get_session, get_blocked_access_tokens_cache, get_active_refresh_tokens_cache
from src.models import User, BlockedAccessToken
from src.services import ServiceMixin
from src.services.auth import Auth

__all__ = ("UserService", "get_user_service")
auth_handler = Auth()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class UserService(ServiceMixin):
    def __init__(
                self, 
                cache: AbstractCache, 
                session: Session,
                blocked_access_tokens_cache: AbstractCache=None,
                active_refresh_tokens_cache: AbstractCache=None,
            ):
            super().__init__(cache=cache, session=session)
            self.blocked_access_tokens_cache = blocked_access_tokens_cache
            self.active_refresh_tokens_cache = active_refresh_tokens_cache

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
                        uuid=str(uuid.uuid4()),
                        roles=['common_user', 'special_guest'])
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
        self.add_refresh_token_to_cache(refresh_token)

        return {'access_token': access_token, 'refresh_token': refresh_token}

    def get_current_user(self, token: str) -> UserModel:
        payload = auth_handler.decode_token(token)
        logger.debug(payload['scope'])
        token_data = TokenPayload(**payload)

        user: Union[dict[str, Any], None] = self.session.query(User).filter(User.username==token_data.sub).one_or_none()

        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Could not find user") 
        user_no_password_field = {key: value for (key, value) in user if key!='password'}
        user_no_password_field['roles'] = user_no_password_field['roles'].replace('}', '').replace('{', '')
        user_no_password_field['roles'] = user_no_password_field['roles'].split(',')
        logger.debug(user_no_password_field['roles'])
        return UserModel(**user_no_password_field)

    def refresh_tokens(self, refresh_token) -> Tokens:
        if not self.check_if_refresh_token_is_active_in_cache(refresh_token=refresh_token):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Current refresh token is no longer active.')
        new_refresh_token = auth_handler.update_refresh_token(refresh_token)
        self.add_refresh_token_to_cache(new_refresh_token)
        username = auth_handler.decode_refresh_token(refresh_token)['sub']
        new_access_token = auth_handler.encode_token(username=username)
        return Tokens(access_token=new_access_token, refresh_token=new_refresh_token)

    def block_user_token(self, access_token):
        jti = auth_handler.decode_token(access_token)['jti']
        if blocked_token := self.blocked_access_tokens_cache.get(key=f"{jti}"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='(Redis) Already logged out!')

        already_blocked = self.session.query(BlockedAccessToken).filter(BlockedAccessToken.jti==jti).one_or_none()
        if already_blocked:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Already logged out!')
        
        try:
            self.blocked_access_tokens_cache.set(key=f"{jti}", value=jti)
            new_blocked_token = BlockedAccessToken(jti=jti)
            self.session.add(new_blocked_token)
            self.session.commit()
            self.session.refresh(new_blocked_token)
            return 'Logged out!'
        except:
            raise HTTPException(status_code=500, detail='Can\'t add access token to database.')

    def check_token_if_blocked(self, access_token):
        jti = auth_handler.decode_token(access_token)['jti']
        if blocked_token := self.blocked_access_tokens_cache.get(key=f"{jti}"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='(Redis) Already logged out!')
        
        already_blocked = self.session.query(BlockedAccessToken).filter(BlockedAccessToken.jti==jti).one_or_none()
        if already_blocked:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Already logged out.')
        return False

    def edit_user(self, access_token, new_user_details: UserCreate) -> Tuple[dict, str]:
        username = auth_handler.decode_token(access_token)['sub']
        user = self.session.query(User).filter(User.username==username).one_or_none()
        if user is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Incorrect user')
        try:
            user.username = new_user_details.username
            user.email = new_user_details.email
            self.session.commit()
            self.session.refresh(user)
            access_token = auth_handler.encode_token(user.username)
            refresh_token = auth_handler.encode_refresh_token(user.username)
            self.add_refresh_token_to_cache(refresh_token)
            user_no_password_field = {key: value for (key, value) in user if key!='password'}
            user_no_password_field['roles'] = user_no_password_field['roles'].replace('}', '').replace('{', '')
            user_no_password_field['roles'] = user_no_password_field['roles'].split(',')
            return user_no_password_field, access_token
        except Exception as e:
            raise HTTPException(status_code=500, detail='Can\'t edit user in database. {}'.format(e))

    def add_refresh_token_to_cache(self, refresh_token):
        username = auth_handler.decode_refresh_token(refresh_token)['sub']
        token_list = []
        if tokens_json := self.active_refresh_tokens_cache.get(key=f"{username}"):
            token_list = json.loads(tokens_json)
        token_list.append(refresh_token)
        new_tokens_json = json.dumps(token_list)
        self.active_refresh_tokens_cache.set(key=f"{username}", value=new_tokens_json)
        logger.debug('Refresh token was saved to cache. (Redis)')

    def delete_refresh_tokens_from_cache(self, access_token):
        username = auth_handler.decode_token(access_token)['sub']
        self.active_refresh_tokens_cache.set(key=f"{username}", value='{}')
        logger.debug('All refresh tokens of this user was revoked. (Redis)')
        return 'Logged out from all devices!'

    def check_if_refresh_token_is_active_in_cache(self, refresh_token):
        username = auth_handler.decode_refresh_token(refresh_token)['sub']
        token_list = []
        if tokens_json := self.active_refresh_tokens_cache.get(key=f"{username}"):
            token_list = json.loads(tokens_json)
        if refresh_token in token_list:
            return True
        return False


# get_user_service — это провайдер UserService. Синглтон
@lru_cache()
def get_user_service(
    cache: AbstractCache = Depends(get_cache),
    session: Session = Depends(get_session),
    blocked_access_tokens_cache: AbstractCache = Depends(get_blocked_access_tokens_cache),
    active_refresh_tokens_cache: AbstractCache = Depends(get_active_refresh_tokens_cache),
) -> UserService:
    return UserService(
                cache = cache,
                session = session,
                blocked_access_tokens_cache = blocked_access_tokens_cache,
                active_refresh_tokens_cache = active_refresh_tokens_cache,
            )
