from typing import Any, TypeVar
from uuid import UUID

from fastapi import HTTPException, status
from phonenumbers import (
    NumberParseException,
    PhoneNumberFormat,
    format_number,
    is_valid_number,
)
from phonenumbers import parse as phone_parse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.constants import DEFAULT_PHONE_REGION
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


def validate_and_format_phone(
    phone: str,
    default_region: str = DEFAULT_PHONE_REGION,
) -> str:
    """Валидация и нормализация номера телефона.

    Парсит переданную строку как телефонный номер, предполагая регион 'RU',
    и при успешной валидации возвращает номер в международном формате
    E.164.

    Допустимые форматы ввода (примеры):
    - "+7 (999) 123-45-67" → "+79991234567"
    - "89991234567"        → "+79991234567"
    - "9991234567"         → "+79991234567"
        (если код города определён как 999)
    - "+1 (555) 111-22-33" → "+15551112233"
        (валидный международный номер)
    - "8-800-555-35-35"    → "+78005553535"

    Если номер не удаётся распознать (например, "abc") или он не является
    валидным по стандартам libphonenumber, поднимается ValueError.

    Raises:
        ValueError: при некорректном формате или невалидном номере.

    Returns:
        str: нормализованный номер в формате E.164
            (например, "+79991234567").

    """
    try:
        parsed_phone = phone_parse(phone, default_region)
    except NumberParseException:
        raise ValueError('Некорректный формат номера телефона.')
    if is_valid_number(parsed_phone):
        return format_number(parsed_phone, PhoneNumberFormat.E164)
    raise ValueError('Номер телефона не является валидным.')
