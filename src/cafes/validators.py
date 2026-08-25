from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.cafes.crud import cafe_crud
from src.cafes.errors import (
    CafeDuplicateError,
    EmptyManagersListError,
    ManagerNotBusyError,
    ManagerNotFoundError,
    ManagerRoleError,
    ManagerWrongCafeError,
)
from src.core.constants import (
    ACCESS_FORBIDDEN_DETAIL,
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

    existing_users_map: dict[UUID, User] = {
        user.id: user for user in existing_users
    }

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


async def check_manager_is_working(manager: User) -> None:
    """Проверяет, привязан ли менеджер хотя бы к 1 кафе.

    Raises:
        ManagerNotBusyError если менеджер не привязан к кафе.

    """
    if manager.cafe_id is None:
        logger.warning(
            'Менеджер %s не привязан ни к одному кафе',
            manager.id,
        )
        raise ManagerNotBusyError(
            f'Менеджер {manager.id} не привязан ни к одному кафе',
        )


async def check_manager_is_working_in_cafe_with_id(
    manager: User,
    cafe_id: UUID,
) -> None:
    """Проверяет, привязан ли менеджер к конкретному кафе.

    Raises:
        ManagerWrongCafeError если менеджер привязан не к тому кафе.

    """
    if manager.cafe_id != cafe_id:
        logger.warning(
            'Менеджер %s не привязан к кафе c id %s',
            manager.id,
            cafe_id,
        )
        raise ManagerWrongCafeError(
            f'Менеджер {manager.id} не привязан к кафе c id {cafe_id}',
        )


async def check_cafe_exists(
    session: AsyncSession,
    cafe_id: UUID,
) -> None:
    """Проверяет существование кафе по ID.

    Args:
        session: Сессия БД
        cafe_id: ID кафе

    Raises:
        HTTPException 404: Если кафе с таким ID не существует

    """
    if not await cafe_crud.exists(session, cafe_id):
        logger.warning('Кафе с id %s не найдено.', cafe_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Кафе не найдено',
        )


async def check_user_cafe_access(
    session: AsyncSession,
    user: User,
    cafe_id: UUID,
) -> None:
    """Проверяет, имеет ли пользователь доступ к управлению кафе.

    ВАЖНО: Эта функция НЕ проверяет роль пользователя.
    Уже проверили пользователя через Depends(get_user_by_role(STAFF_ROLE)).

    Правила доступа:
        - ADMIN: имеет доступ к ЛЮБОМУ кафе
        - MANAGER: имеет доступ ТОЛЬКО к своему кафе (user.cafe_id == cafe_id)

    Args:
        session: Сессия БД
        user: Текущий пользователь (уже проверен на принадлежность к STAFF)
        cafe_id: ID кафе, к которому запрашивается доступ

    Raises:
        HTTPException 404: Если кафе с таким ID не существует
        HTTPException 403: Если у пользователя нет прав на это кафе

    """
    await check_cafe_exists(session=session, cafe_id=cafe_id)

    if user.role == Role.ADMIN:
        return
    if user.role == Role.MANAGER:
        if user.cafe_id != cafe_id:
            logger.warning(
                'Пользователь %s не имеет прав на работу с кафе %s',
                user.id,
                cafe_id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ACCESS_FORBIDDEN_DETAIL,
            )
        return
