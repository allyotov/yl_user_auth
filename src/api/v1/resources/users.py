import logging

from http import HTTPStatus
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from src.api.v1.schemas import UserCreate, UserListResponse, UserModel, UserCreated
from src.services import UserService, get_user_service

router = APIRouter()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@router.post(
    path="/signup",
    response_model=UserCreated,
    summary="Зарегистрироваться",
    tags=["auth"],
)
def signup(user: UserCreate, user_service: UserService = Depends(get_user_service),) -> UserCreated:
    logger.debug(user)
    user = user_service.signup(user_details=user)
    logger.debug(user)
    return UserCreated(username=user['username'], email=user['email'])