from typing import Any, TypeVar
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import get_logger
from src.crud.crud import CRUDBase
from src.db.base import Base

ModelType = TypeVar('ModelType', bound=Base)

logger = get_logger(__name__)


async def get_by_id_or_404(
    session: AsyncSession,
    model: type[ModelType],
    obj_id: UUID,
    detail: str = 'Данные не найдены',
    log_msg: str | None = None,
) -> ModelType:
    """Получение объекта по первичному ключу или HTTP 404.

    Использовать когда не нужны дополнительные фильтры.
    """
    obj = await session.get(model, obj_id)
    if not obj:
        if log_msg:
            logger.warning(log_msg)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )
    return obj


async def get_or_404(
    session: AsyncSession,
    crud: CRUDBase,
    obj_id: UUID,
    detail: str = 'Данные не найдены',
    filters: dict[str, Any] | None = None,
    log_msg: str | None = None,
) -> ModelType:
    """Получение объекта через CRUD с опциональными фильтрами или HTTP 404.

    Использовать когда нужна фильтрация (is_active, cafe_id и т.д.).
    """
    obj = await crud.get(session, obj_id, filters=filters)
    if not obj:
        if log_msg:
            logger.warning(log_msg)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )
    return obj
