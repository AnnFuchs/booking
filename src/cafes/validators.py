from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.cafes.crud import cafe_crud
from src.cafes.errors import (
    CafeDuplicateError,
    EmptyManagersListError,
    ManagerNotFoundError,
    ManagerRoleError,
)
from src.core.constants import (
    MESSAGE_DUPLICATE_NAME_AND_ADDRESS,
    MESSAGE_MANAGERS_ID_IS_NULL,
    Role,
)
from src.core.logger import get_logger
from src.db.models_for_alembic import User
from src.users.crud import user_crud

logger = get_logger(__name__)


async def validate_cafe_name_address_unique(
    name: str,
    address: str,
    session: AsyncSession,
    exclude_id: UUID | None = None,
) -> None:
    """Проверяет, что связка name + address уникальна.

    Args:
        name: Название кафе
        address: Адрес кафе
        session: Сессия БД
        exclude_id: ID кафе, которое нужно исключить из проверки
                    (используется при обновлении)

    """
    potential_duplicate = await cafe_crud.get_by_name_and_adress(
        name=name,
        address=address,
        session=session,
    )
    if potential_duplicate and potential_duplicate.id != exclude_id:
        logger.warning(
            'Кафе с названием %s и адресом %s уже есть в базе данных',
            name,
            address,
        )
        raise CafeDuplicateError(MESSAGE_DUPLICATE_NAME_AND_ADDRESS)


async def validate_managers_id(
    session: AsyncSession,
    managers_id: list[UUID],
    required_role: Role,
) -> dict[UUID, User]:
    """Валидация списка managers_id."""
    if not managers_id:
        logger.warning('Передан пустой список менеджеров.')
        raise EmptyManagersListError(MESSAGE_MANAGERS_ID_IS_NULL)

    existing_users = await user_crud.get_multi(
        session=session,
        filters={'id__in': managers_id},
    )

    existing_users_map = {user.id: user for user in existing_users}

    for manager_id in managers_id:
        user = existing_users_map.get(manager_id)
        if user is None:
            logger.warning('Пользователь с id %s не найден.', manager_id)
            raise ManagerNotFoundError(f'Менеджер с id {manager_id} не найден')
        if user.role != required_role:
            logger.warning(
                'Пользователь %s не является менеджером.',
                manager_id,
            )
            raise ManagerRoleError(
                f'Роль пользователя {manager_id} не корректна',
            )

    return existing_users_map
