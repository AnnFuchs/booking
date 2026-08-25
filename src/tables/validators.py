import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.cafes.validators import (
    check_cafe_exists,
    check_manager_is_working_in_cafe_with_id,
)
from src.core.constants import MANAGER_ROLE, STAFF_ROLE
from src.db.models_for_alembic import User


async def check_access_and_build_filters(
    session: AsyncSession,
    current_user: User,
    cafe_id: uuid.UUID,
    is_active: bool | None = None,
) -> dict[str, Any]:
    """Проверка прав доступа и построение фильтров.

    - Проверяет существование кафе (404 если не найдено)
    - Для менеджера проверяет принадлежность к кафе
    - Строит фильтры по роли пользователя
    """
    await check_cafe_exists(session=session, cafe_id=cafe_id)

    if current_user.role in MANAGER_ROLE:
        await check_manager_is_working_in_cafe_with_id(
            manager=current_user,
            cafe_id=cafe_id,
        )

    filters: dict[str, Any] = {'cafe_id': cafe_id}
    if current_user.role in STAFF_ROLE:
        if is_active is not None:
            filters['is_active'] = is_active
    else:
        filters['is_active'] = True

    return filters
