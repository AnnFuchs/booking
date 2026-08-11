import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.cafes.crud import cafe_crud
from src.cafes.errors import CafeManagerAlreadyBusyError
from src.cafes.schemas import CafeCreate, CafeUpdate
from src.cafes.validators import (
    validate_cafe_name_address_unique,
    validate_managers_id,
)
from src.core.constants import Role
from src.core.logger import get_logger
from src.db.models_for_alembic import Cafe, User
from src.db.utils import get_or_404

logger = get_logger(__name__)


async def _assign_managers(
    session: AsyncSession,
    cafe: Cafe,
    managers_id: list[uuid.UUID],
) -> None:
    """Назначает менеджеров кафе, обновляя их cafe_id.

    Raises:
        ManagerNotFoundError: Если менеджер с указанным ID не найден.
        ManagerRoleError: Если пользователь не является менеджером.
        CafeManagerAlreadyBusyError: Если менеджер уже привязан к другому кафе.

    """
    unique_ids = list(set(managers_id))

    if cafe.managers is not None:
        for manager in cafe.managers:
            if manager.id not in unique_ids:
                manager.cafe_id = None

    valid_managers = await validate_managers_id(
        session=session,
        managers_id=unique_ids,
        required_role=Role.MANAGER,
    )

    for manager_id in unique_ids:
        user = valid_managers[manager_id]
        if user.cafe_id is not None and user.cafe_id != cafe.id:
            logger.warning(
                'Менеджер %s уже назначен на кафе %s',
                manager_id,
                user.cafe_id,
            )
            raise CafeManagerAlreadyBusyError(
                f'Менеджер {manager_id} уже назначен на кафе {user.cafe_id}',
            )
        user.cafe_id = cafe.id


class CafeService:
    """Сервисный слой для работы с кафе."""

    async def create_cafe(
        self,
        obj_in: CafeCreate,
        current_user: User,
        session: AsyncSession,
    ) -> Cafe:
        """Создание кафе.

        Только для администраторов и менеджеров
        """
        logger.debug(
            'Пользователь %s создаёт кафе "%s".',
            current_user.id,
            obj_in.name,
        )

        await validate_cafe_name_address_unique(
            name=obj_in.name,
            address=obj_in.address,
            session=session,
        )

        cafe = await cafe_crud.create(
            session=session,
            obj_in=obj_in,
            exclude_fields={'managers_id'},
            commit=False,
        )

        logger.debug('Запланировано создание кафе %s.', cafe.id)

        if obj_in.managers_id:
            await _assign_managers(session, cafe, obj_in.managers_id)
            logger.debug(
                'Назначены менеджеры %s для кафе %s.',
                obj_in.managers_id,
                cafe.id,
            )

        await session.commit()
        await session.refresh(cafe)

        logger.debug('Создано кафе %s.', cafe.id)

        return cafe

    async def get_cafes(
        self,
        current_user: User,
        session: AsyncSession,
        is_active: bool | None = None,
    ) -> list[Cafe]:
        """Получение списка кафе.

        Юзеры - получает все активные кафе
        Менеджеры - получает только то кафе в котором он работает работает
        Администраторы - получает все кафе
        """
        filters: dict[str, Any] = {}

        match current_user.role:
            case Role.ADMIN:
                if is_active is not None:
                    filters['is_active'] = is_active

            case Role.MANAGER:
                filters['id'] = current_user.cafe_id
                if is_active is not None:
                    filters['is_active'] = is_active

            case _:
                filters['is_active'] = True

        cafes = await cafe_crud.get_multi(
            session=session,
            filters=filters or None,
        )
        logger.debug(
            'Получено %d кафе для пользователя %s',
            len(cafes),
            current_user.id,
        )
        return cafes

    async def get_cafe(
        self,
        cafe_id: uuid.UUID,
        current_user: User,
        session: AsyncSession,
    ) -> Cafe:
        """Получение одного кафе.

        Юзеры - получает кафе по ID, только если оно активно
        Менеджеры - получает кафе по ID, только если он в нем работает
        Администраторы - Получает кафе в любом случае
        """
        filters: dict[str, Any] = {}

        match current_user.role:
            case Role.USER:
                filters['is_active'] = True

            case Role.MANAGER:
                filters['id'] = current_user.cafe_id

            case _:
                pass

        cafe = await get_or_404(
            session,
            cafe_crud,
            cafe_id,
            detail='Данные не найдены',
            filters=filters or None,
            log_msg=f'Кафе с id {cafe_id} не найдено.',
        )
        logger.debug(
            'Получено кафе %s для пользователя %s',
            cafe_id,
            current_user.id,
        )
        return cafe

    async def update_cafe(
        self,
        cafe_id: uuid.UUID,
        data: CafeUpdate,
        current_user: User,
        session: AsyncSession,
    ) -> Cafe:
        """Обновление кафе.

        Менеджер - только свое кафе
        Администратор - любое кафе
        """
        logger.debug(
            'Пользователь %s обновляет кафе %s.',
            current_user.id,
            cafe_id,
        )
        cafe = await self.get_cafe(
            cafe_id=cafe_id,
            current_user=current_user,
            session=session,
        )

        if data.name or data.address:
            await validate_cafe_name_address_unique(
                name=data.name or cafe.name,
                address=data.address or cafe.address,
                session=session,
                exclude_id=cafe_id,
            )

        # update_data_without_managers = data.model_copy(
        #     update={'managers_id': None},
        # )
        updated_cafe = await cafe_crud.update(
            db_obj=cafe,
            obj_in=data,
            session=session,
            exclude_fields={'managers_id'},
        )
        if data.managers_id is not None:
            await _assign_managers(session, updated_cafe, data.managers_id)
            logger.debug(
                'Обновлены менеджеры %s для кафе %s.',
                data.managers_id,
                cafe_id,
            )
        await session.refresh(updated_cafe)
        logger.debug('Обновлено кафе %s.', cafe_id)
        return updated_cafe


cafe_service = CafeService()
