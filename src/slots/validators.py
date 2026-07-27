import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.cafes.crud import cafe_crud
from src.core.constants import (
    ACCESS_FORBIDDEN_DETAIL,
    Role,
)
from src.core.logger import get_logger
from src.users.models import User

logger = get_logger(__name__)


async def check_user_cafe_access(
    session: AsyncSession,
    user: User,
    cafe_id: uuid.UUID,
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
    cafe = await cafe_crud.get(session, cafe_id)
    if not cafe:
        logger.warning('Кафе с id %s не найдено.', cafe_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Данные не найдены',
        )
    if user.role == Role.ADMIN:
        return
    if user.role == Role.MANAGER:
        if user.cafe_id != cafe.id:
            logger.warning(
                'Пользователь %s не имеет прав на работу с кафе %s',
                user.id,
                cafe.id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ACCESS_FORBIDDEN_DETAIL,
            )
        return
