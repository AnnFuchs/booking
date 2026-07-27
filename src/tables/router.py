import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_user_by_role
from src.core.constants import ALL_ROLE, STAFF_ROLE
from src.db.models_for_alembic import User
from src.db.session import get_async_session
from src.tables.schemas import TableCreate, TableInfo, TableUpdate
from src.tables.service import table_service

router = APIRouter(
    prefix='/cafes/{cafe_id}/tables',
    tags=['Столы'],
)

SessionDep = Annotated[AsyncSession, Depends(get_async_session)]


@router.post(
    '',
    response_model=TableInfo,
    summary='Новый стол в кафе.',
    status_code=status.HTTP_201_CREATED,
)
async def create_table(
    cafe_id: uuid.UUID,
    data: TableCreate,
    session: SessionDep,
    current_user: User = Depends(get_user_by_role(STAFF_ROLE)),
) -> TableInfo:
    """Создает новый стол в кафе.

    Только для администраторов и менеджеров
    """
    return await table_service.create_table(
        cafe_id=cafe_id,
        data=data,
        current_user=current_user,
        session=session,
    )


@router.get(
    '',
    response_model=list[TableInfo],
    summary='Список столов в кафе.',
)
async def get_tables(
    cafe_id: uuid.UUID,
    session: SessionDep,
    show_active: bool = Query(default=True),
    current_user: User = Depends(get_user_by_role(ALL_ROLE)),
) -> list[TableInfo]:
    """Получение списка столов в кафе.

    Для администратора — все столы (с фильтрацией show_active)
    Для менеджера — только своё кафе
    Для пользователей — только активные
    """
    return await table_service.get_tables(
        session=session,
        cafe_id=cafe_id,
        current_user=current_user,
        is_active=show_active,
    )


@router.get(
    '/{table_id}',
    response_model=TableInfo,
    summary='Информация о столе в кафе по его ID',
)
async def get_table(
    cafe_id: uuid.UUID,
    table_id: uuid.UUID,
    session: SessionDep,
    current_user: User = Depends(get_user_by_role(ALL_ROLE)),
) -> TableInfo:
    """Получение информации о столе.

    Для администратора и менеджер — любые столы
    Для пользователей — только активные
    """
    return await table_service.get_table(
        session=session,
        cafe_id=cafe_id,
        table_id=table_id,
        current_user=current_user,
    )


@router.patch(
    '/{table_id}',
    response_model=TableInfo,
    summary='Обновление информации о столе',
)
async def update_table(
    cafe_id: uuid.UUID,
    table_id: uuid.UUID,
    data: TableUpdate,
    session: SessionDep,
    current_user: User = Depends(get_user_by_role(STAFF_ROLE)),
) -> TableInfo:
    """Обновление стола.

    Только для администраторов и менеджеров
    """
    return await table_service.update_table(
        cafe_id=cafe_id,
        table_id=table_id,
        data=data,
        current_user=current_user,
        session=session,
    )
