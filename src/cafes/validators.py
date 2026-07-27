import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.cafes.errors import (
    CafeDuplicateError,
    DuplicateManagersError,
    EmptyManagersListError,
)
from src.core.constants import (
    MESSAGE_DUPLICATE_NAME_AND_ADDRESS,
    MESSAGE_MANAGERS_ID_DUPLICATE,
    MESSAGE_MANAGERS_ID_IS_NULL,
)
from src.core.logger import get_logger
from src.db.models_for_alembic import Cafe

logger = get_logger(__name__)


async def validate_cafe_name_address_unique(
    name: str,
    address: str,
    session: AsyncSession,
    exclude_id: uuid.UUID | None = None,  # чтобы исключить самого себя
) -> None:
    """Проверяет, что связка name + address уникальна.

    Args:
        name: Название кафе
        address: Адрес кафе
        session: Сессия БД
        exclude_id: ID кафе, которое нужно исключить из проверки
                    (используется при обновлении)

    """
    query = select(Cafe).where(
        Cafe.name == name,
        Cafe.address == address,
    )
    if exclude_id is not None:
        query = query.where(Cafe.id != exclude_id)
    result = await session.execute(query)
    cafe = result.scalars().first()
    if cafe:
        logger.warning(
            'Кафе с названием %s и адресом %s уже есть в базе данных',
            name,
            address,
        )
        raise CafeDuplicateError(MESSAGE_DUPLICATE_NAME_AND_ADDRESS)


def validate_managers_id(
    value: list[uuid.UUID] | None,
) -> list[uuid.UUID] | None:
    """Проверка списка managers_id на пустоту и дубликаты.

    Args:
    value: Список ID менеджеров

    Returns:
        list[uuid.UUID] | None: Исходный список без изменений

    Raises:
        EmptyManagersListError: Если список пуст
        DuplicateManagersError: Если в списке есть дубликаты

    """
    if value is None:
        logger.debug('Передан пустой список.')
        return value

    if not value:
        logger.warning('Cписок менеджеров не передан.')
        raise EmptyManagersListError(MESSAGE_MANAGERS_ID_IS_NULL)

    if len(value) != len(set(value)):
        logger.warning('В списке менеджеров дубликаты.')
        raise DuplicateManagersError(MESSAGE_MANAGERS_ID_DUPLICATE)

    return value
