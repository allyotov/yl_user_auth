from http import HTTPStatus
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from src.api.v1.schemas import UserCreate, UserListResponse, UserModel
from src.services import AuthService, get_auth_service

router = APIRouter()


@router.post(
    path="/signup",
    response_model=UserModel,
    summary="Зарегистрироваться",
    tags=["auth"],
)
def signup(
    user: UserCreate, auth_service: AuthService = Depends(get_auth_service),
) -> UserModel:
    user: dict = auth_service.signup(user=user)
    return UserModel(**user)