import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.cafes.validators import check_user_cafe_access
from src.core.logger import get_logger
from src.db.models_for_alembic import Table, User
from src.tables.crud import table_crud
from src.tables.errors import TableNotFoundError
from src.tables.schemas import TableCreate, TableUpdate
from src.tables.validators import check_access_and_build_filters

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
        await check_user_cafe_access(
            session=session,
            user=current_user,
            cafe_id=cafe_id,
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
        is_active: bool | None = None,
    ) -> list[Table]:
        """Получение списка доступных для бронирования столов в кафе.

        Для юзера - только активные
        Для администратора - любые
        Для менеджера - любые, но только в своем кафе
        """
        filters = await check_access_and_build_filters(
            session=session,
            current_user=current_user,
            cafe_id=cafe_id,
            is_active=is_active,
        )

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
        filters = await check_access_and_build_filters(
            session=session,
            current_user=current_user,
            cafe_id=cafe_id,
            is_active=is_active,
        )

        table = await table_crud.get(
            session=session,
            obj_id=table_id,
            filters=filters,
        )

        if not table:
            logger.warning(
                'Стол с id %s и фильтрами %s не найден.',
                table_id,
                filters,
            )
            raise TableNotFoundError(f'Стол с id {table_id} не найден')

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
        table = await self.get_table(
            session=session,
            cafe_id=cafe_id,
            table_id=table_id,
            current_user=current_user,
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
