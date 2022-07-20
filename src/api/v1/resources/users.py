import logging

from fastapi import APIRouter, Depends, Security
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials

from src.api.v1.schemas import UserCreate, UserModel, UserCreated, UserAuth, Tokens, Message, EditProfileResult
from src.services import UserService, get_user_service

router = APIRouter()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

reuseable_oauth = OAuth2PasswordBearer(tokenUrl='/login', scheme_name='JWT')
# reuseable_oauth_refresh = OAuth2PasswordBearer(tokenUrl='/refresh', scheme_name='JWT')
security = HTTPBearer()


@router.post(path="/signup", response_model=UserCreated, summary="Зарегистрироваться", tags=["auth"], status_code=201)
def signup(user: UserCreate, user_service: UserService = Depends(get_user_service),) -> UserCreated:
    logger.debug(user)
    user = user_service.signup(user_details=user)
    logger.debug(user)
    return UserCreated(username=user['username'], email=user['email'])


@router.post(path="/login", response_model=Tokens, summary="Войти", tags=["auth"],)
def login(user: UserAuth, user_service: UserService = Depends(get_user_service),) -> Tokens:
    logger.debug(user)
    tokens = user_service.login(user_details=user)
    logger.debug(tokens)
    return Tokens(**tokens)


@router.post(path="/refresh", response_model=Tokens, summary="Посмотреть информацию о себе", tags=["auth"],)
def refresh(
    credentials: HTTPAuthorizationCredentials = Security(security), 
    user_service: UserService = Depends(get_user_service),
    ) -> Tokens:
    refresh_token = credentials.credentials
    return user_service.refresh_tokens(refresh_token=refresh_token)


@router.get(path="/users/me", response_model=UserModel, summary="Посмотреть информацию о себе", tags=["auth"],)
def get_me(token: str = Depends(reuseable_oauth), user_service: UserService = Depends(get_user_service),) -> UserModel:
    user_service.check_token_if_blocked(token)
    return user_service.get_current_user(token)


@router.patch(path="/users/me", response_model=EditProfileResult, summary="Отредактировать свой профиль", tags=["auth"],)
def edit_profile(
        user: UserCreated, 
        credentials: HTTPAuthorizationCredentials = Security(security),
        user_service: UserService = Depends(get_user_service),) -> EditProfileResult:
    access_token = credentials.credentials
    user_service.check_token_if_blocked(access_token)
    edited_user, access_token = user_service.edit_user(access_token=access_token, new_user_details=user)
    return EditProfileResult(
        msg='Update is successful. Please use new access_token.',
        user=edited_user,
        access_token=access_token
        )


@router.post(path="/logout", response_model=Message, summary="Выйти", tags=["auth"],)
def logout(token: str = Depends(reuseable_oauth), user_service: UserService = Depends(get_user_service),) -> Message:
    logger.debug(token)
    return Message(msg=user_service.block_user_token(token))
