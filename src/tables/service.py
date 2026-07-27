import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.cafes.crud import cafe_crud
from src.core.constants import Role
from src.core.logger import get_logger
from src.db.models_for_alembic import Table, User
from src.tables.crud import table_crud
from src.tables.schemas import TableCreate, TableUpdate

logger = get_logger(__name__)


class TableService:
    """Сервисный слой для работы со столами."""

    async def create_table(
        self,
        cafe_id: uuid.UUID,
        data: TableCreate,
        current_user: User,
        session: AsyncSession,
    ) -> Table:
        """Создание стола.

        Менеджер - только в своем кафе
        Администратор - в любом кафе
        """
        cafe = await cafe_crud.get(
            obj_id=cafe_id,
            session=session,
        )
        if not cafe:
            logger.warning(
                'Кафе с id %s не найдено.',
                cafe_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Кафе не найдено.',
            )

        if (
            current_user.role == Role.MANAGER
            and current_user.cafe_id != cafe.id
        ):
            logger.warning(
                'Пользователь %s не имеет доступа к кафе %s.',
                current_user.id,
                cafe_id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Доступ запрещен',
            )

        table = await table_crud.create(
            obj_in=data,
            session=session,
            cafe_id=cafe_id,
        )
        logger.debug('Создан стол %s в кафе %s', table.id, cafe_id)
        return table

    async def get_tables(
        self,
        session: AsyncSession,
        cafe_id: uuid.UUID,
        current_user: User,
        is_active: bool,
    ) -> list[Table]:
        """Получение списка доступных для бронирования столов в кафе.

        Для юзера - только активные
        Для администратора - любые
        Для менеджера - только в своем кафе
        """
        cafe = await cafe_crud.get(
            obj_id=cafe_id,
            session=session,
        )
        if not cafe:
            logger.warning(
                'Кафе с id %s не найдено.',
                cafe_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Кафе не найдено.',
            )

        filters: dict[str, Any] = {
            'cafe_id': cafe.id,
        }

        match current_user.role:
            case Role.MANAGER:
                if current_user.cafe_id != cafe_id:
                    logger.warning(
                        'Пользователь %s не имеет доступа к кафе %s.',
                        current_user.id,
                        cafe_id,
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail='Доступ запрещен',
                    )
                filters['is_active'] = is_active

            case Role.ADMIN:
                filters['is_active'] = is_active

            case _:
                filters['is_active'] = True

        tables = await table_crud.get_multi(
            session=session,
            filters=filters,
        )
        logger.debug(
            'Получены столы (%s шт.) кафе %s для пользователя %s',
            len(tables),
            cafe_id,
            current_user.id,
        )
        return tables

    async def get_table(
        self,
        session: AsyncSession,
        cafe_id: uuid.UUID,
        table_id: uuid.UUID,
        current_user: User,
        is_active: bool | None = None,
    ) -> Table:
        """Получение информации о столе в кафе по его ID.

        Для пользователя - только активные
        Для менеджера - только в своем кафе (любые)
        Для администратора - в любом кафе (любые)
        """
        cafe = await cafe_crud.get(
            obj_id=cafe_id,
            session=session,
        )
        if not cafe:
            logger.warning(
                'Кафе с id %s не найдено.',
                cafe_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Кафе не найдено.',
            )

        table = await table_crud.get(
            obj_id=table_id,
            session=session,
        )
        if not table:
            logger.warning(
                'Стол с id %s не найден.',
                cafe_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Стол не найден.',
            )

        if table.cafe_id != cafe_id:
            logger.warning(
                'Стол с id %s не найден в кафе %s',
                table_id,
                cafe_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Стол не найден в этом кафе',
            )

        filters: dict[str, Any] = {}

        match current_user.role:
            case Role.ADMIN:
                if is_active is not None:
                    filters['is_active'] = is_active

            case Role.MANAGER:
                if current_user.cafe_id != cafe_id:
                    logger.warning(
                        'Пользователь %s не имеет доступа к кафе %s.',
                        current_user.id,
                        cafe_id,
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail='Доступ запрещен',
                    )
                if is_active is not None:
                    filters['is_active'] = is_active

            case _:
                filters['is_active'] = True

        table = await table_crud.get(
            session=session,
            obj_id=table_id,
            filters=filters or None,
        )
        if table is None:
            logger.warning(
                'Стол %s недоступен для пользователя %s (is_active фильтр)',
                table_id,
                current_user.id,
            )

        logger.debug(
            'Получен стол %s кафе %s для пользователя %s',
            table_id,
            cafe_id,
            current_user.id,
        )
        return table

    async def update_table(
        self,
        cafe_id: uuid.UUID,
        table_id: uuid.UUID,
        data: TableUpdate,
        current_user: User,
        session: AsyncSession,
    ) -> Table:
        """Обновление информации о столе в кафе по его ID.

        Только для администраторов и менеджеров
        Для менеджеров - только в своем кафе
        Для администраторов - в любом кафе
        """
        table = await table_crud.get(
            obj_id=table_id,
            session=session,
        )
        if not table:
            logger.warning(
                'Стол с id %s не найден.',
                cafe_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Стол не найден.',
            )

        if (
            current_user.role == Role.MANAGER
            and table.cafe_id != current_user.cafe_id
        ):
            logger.warning(
                'Пользователь %s не имеет доступа к кафе %s.',
                current_user.id,
                cafe_id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Доступ запрещен',
            )

        table = await table_crud.update(
            db_obj=table,
            obj_in=data,
            session=session,
        )
        logger.debug(
            'Пользователем %s обновлен стол %s кафе %s.',
            current_user.id,
            table.id,
            table.cafe_id,
        )
        return table


table_service = TableService()
