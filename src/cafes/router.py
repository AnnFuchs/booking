import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_user_by_role
from src.cafes.errors import (
    CafeDuplicateError,
    CafeManagerAlreadyBusyError,
    CafeNotFoundError,
    EmptyManagersListError,
    ManagerNotBusyError,
    ManagerNotFoundError,
    ManagerRoleError,
)
from src.cafes.router_responses import (
    CAFES_LIST_RESPONSES,
    CAFE_CREATE_RESPONSES,
    CAFE_GET_BY_ID_RESPONSES,
    CAFE_UPDATE_RESPONSES,
)
from src.cafes.schemas import CafeCreate, CafeInfo, CafeUpdate
from src.cafes.service import cafe_service
from src.core.constants import ALL_ROLE, STAFF_ROLE
from src.db.models_for_alembic import User
from src.db.session import get_async_session

router = APIRouter(prefix='/cafes', tags=['Кафе'])

SessionDep = Annotated[AsyncSession, Depends(get_async_session)]


@router.post(
    '',
    response_model=CafeInfo,
    summary='Создание нового кафе',
    status_code=status.HTTP_201_CREATED,
    responses=CAFE_CREATE_RESPONSES,
)
async def create_cafe(
    session: SessionDep,
    cafe_in: CafeCreate,
    current_user: User = Depends(get_user_by_role(STAFF_ROLE)),
) -> CafeInfo:
    """Создает новое кафе."""
    try:
        return await cafe_service.create_cafe(
            obj_in=cafe_in,
            current_user=current_user,
            session=session,
        )
    except (
        CafeDuplicateError,
        EmptyManagersListError,
        ManagerRoleError,
        CafeManagerAlreadyBusyError,
        ValueError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )
    except ManagerNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )


@router.get(
    '',
    response_model=list[CafeInfo],
    summary='Получение списка кафе',
    responses=CAFES_LIST_RESPONSES,
)
async def get_cafes(
    session: SessionDep,
    is_active: bool = Query(default=True),
    current_user: User = Depends(get_user_by_role(ALL_ROLE)),
) -> list[CafeInfo]:
    """Возвращает информацию о всех кафе.

    Для администраторов — все кафе (с фильтрацией is_active)
    Для менеджеров — только своё кафе
    Для пользователей — только активные кафе
    """
    try:
        return await cafe_service.get_cafes(
            current_user=current_user,
            session=session,
            is_active=is_active,
        )
    except ManagerNotBusyError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.get(
    '/{cafe_id}',
    response_model=CafeInfo,
    summary='Получение информации о кафе по его ID',
    responses=CAFE_GET_BY_ID_RESPONSES,
)
async def get_cafe_by_id(
    session: SessionDep,
    cafe_id: uuid.UUID,
    current_user: User = Depends(get_user_by_role(ALL_ROLE)),
) -> CafeInfo:
    """Возвращает информацию о кафе по его ID."""
    try:
        return await cafe_service.get_cafe(
            cafe_id=cafe_id,
            current_user=current_user,
            session=session,
        )
    except CafeNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )
    except ManagerNotBusyError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.patch(
    '/{cafe_id}',
    response_model=CafeInfo,
    summary='Обновление кафе по его ID',
    responses=CAFE_UPDATE_RESPONSES,
)
async def update_cafe(
    session: SessionDep,
    cafe_id: uuid.UUID,
    data: CafeUpdate,
    current_user: User = Depends(get_user_by_role(STAFF_ROLE)),
) -> CafeInfo:
    """Обновляет кафе.

    Только для администраторов и менеджеров
    """
    try:
        return await cafe_service.update_cafe(
            cafe_id=cafe_id,
            data=data,
            current_user=current_user,
            session=session,
        )
    except (CafeNotFoundError, ManagerNotFoundError) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )
    except (
        CafeDuplicateError,
        ManagerNotBusyError,
        ValueError,
        CafeManagerAlreadyBusyError,
        EmptyManagersListError,
        ManagerRoleError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )
