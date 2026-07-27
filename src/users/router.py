from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import (
    get_user_by_role,
)
from src.core.constants import ALL_ROLE, STAFF_ROLE
from src.db.session import get_async_session
from src.users.errors import (
    ContactInfoMissingError,
    DuplicateInfoError,
    InsufficientPrivilegesError,
    SelfDeactivationAttemptError,
    UserDataConflictError,
)
from src.users.models import User
from src.users.router_responses import (
    USERS_CREATE_RESPONSES,
    USERS_LIST_RESPONSES,
    USER_GET_BY_ID_RESPONSES,
    USER_GET_ME_RESPONSES,
    USER_UPDATE_BY_ID_RESPONSES,
    USER_UPDATE_ME_RESPONSES,
)
from src.users.schemas import UserCreate, UserInfo, UserUpdate, UserUpdateAdmin
from src.users.service import user_service
from src.users.validators import check_user_exists

router = APIRouter(prefix='/users', tags=['Пользователи'])

SessionDep = Annotated[AsyncSession, Depends(get_async_session)]


@router.get(
    '',
    response_model=list[UserInfo],
    summary='Получение списка пользователей',
    dependencies=[Depends(get_user_by_role(STAFF_ROLE))],
    responses=USERS_LIST_RESPONSES,
)
async def get_all_users(session: SessionDep) -> list[UserInfo]:
    """Возвращает информацию о всех пользователях.

    Только для администраторов или менеджеров
    """
    return await user_service.get_multi_users(session)


@router.post(
    '',
    response_model=UserInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Регистрация нового пользователя',
    dependencies=[Depends(get_user_by_role(STAFF_ROLE, allow_anon=True))],
    responses=USERS_CREATE_RESPONSES,
)
async def create_user(
    user_in: UserCreate,
    session: SessionDep,
) -> UserInfo:
    """Создает нового пользователя с указанными данными.

    Регистрировать пользователя может или не авторизированный пользователь
    или менеджер или администратор.
    Обязательные поля:
    - username
    - password
    - email или phone
    """
    try:
        return await user_service.create(session, user_in)
    except DuplicateInfoError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Ошибка при создании пользователя.',
        )


@router.get(
    '/me',
    response_model=UserInfo,
    summary='Получение информации о текущем пользователе',
    responses=USER_GET_ME_RESPONSES,
)
async def get_your_user_info(
    current_user: User = Depends(get_user_by_role(ALL_ROLE, allow_anon=False)),
) -> UserInfo:
    """Возвращает информацию о текущем пользователе.

    Только для авторизированных пользователей
    """
    return current_user


@router.patch(
    '/me',
    response_model=UserInfo,
    summary='Обновление информации о текущем пользователе',
    responses=USER_UPDATE_ME_RESPONSES,
)
async def update_your_user_info(
    update_data: UserUpdate,
    session: SessionDep,
    user: User = Depends(get_user_by_role(ALL_ROLE, allow_anon=False)),
) -> UserInfo:
    """Возвращает обновленную информацию о пользователе.

    Только для авторизированных пользователей
    """
    try:
        return await user_service.update(
            session=session,
            db_user=user,
            update_data=update_data,
            request_author=user,
        )
    except ContactInfoMissingError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Необходимо указать email или телефон.',
        )
    except SelfDeactivationAttemptError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Запрещено деактивировать собственный аккаунт.',
        )
    except DuplicateInfoError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Ошибка при создании пользователя.',
        )
    except InsufficientPrivilegesError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав для осуществления операции.',
        )


@router.get(
    '/{user_id}',
    response_model=UserInfo,
    summary='Получение информации о пользователе по его id',
    dependencies=[Depends(get_user_by_role(STAFF_ROLE))],
    responses=USER_GET_BY_ID_RESPONSES,
)
async def get_user_by_id(user_id: UUID, session: SessionDep) -> UserInfo:
    """Возвращает информацию о пользователе по его ID.

    Только для администраторов или менеджеров
    """
    return await user_service.get_user(session, user_id)


@router.patch(
    '/{user_id}',
    response_model=UserInfo,
    summary='Обновление информации о пользователе по его id',
    responses=USER_UPDATE_BY_ID_RESPONSES,
)
async def update_user_by_id(
    user_id: UUID,
    update_data: UserUpdateAdmin,
    session: SessionDep,
    request_author: User = Depends(get_user_by_role(STAFF_ROLE)),
) -> UserInfo:
    """Возвращает обновленную информацию о пользователе по его ID.

    Только для администраторов или менеджеров.
    """
    db_user = await check_user_exists(user_id=user_id, session=session)
    try:
        return await user_service.update(
            session=session,
            db_user=db_user,
            update_data=update_data,
            request_author=request_author,
        )
    except ContactInfoMissingError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Необходимо указать email или телефон.',
        )
    except SelfDeactivationAttemptError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Запрещено деактивировать собственный аккаунт.',
        )
    except (DuplicateInfoError, UserDataConflictError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Ошибка при создании пользователя.',
        )
    except InsufficientPrivilegesError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав для осуществления операции.',
        )
