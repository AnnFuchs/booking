import uuid
from datetime import datetime
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
)

from src.core.constants import (
    ADDRESS_MAX_LEN,
    DESCRIPTION_MAX_LEN,
    E164_RU_NUMBER,
    MIN_LEN,
    NAME_MAX_LEN,
)
from src.users.schemas import UserShortInfo


class CafeBase(BaseModel):
    """Базовая схема кафе."""

    name: str = Field(
        min_length=MIN_LEN,
        max_length=NAME_MAX_LEN,
    )
    address: str = Field(
        min_length=MIN_LEN,
        max_length=ADDRESS_MAX_LEN,
    )
    phone: E164_RU_NUMBER
    description: str | None = Field(
        None,
        max_length=DESCRIPTION_MAX_LEN,
    )
    photo_id: uuid.UUID | None = None


class CafeCreate(CafeBase):
    """Схема для создания нового кафе."""

    managers_id: list[uuid.UUID]


class CafeUpdate(BaseModel):
    """Схема для частичного обновления кафе."""

    name: str | None = Field(
        default=None,
        max_length=NAME_MAX_LEN,
    )
    address: str | None = Field(
        default=None,
        max_length=ADDRESS_MAX_LEN,
    )
    phone: E164_RU_NUMBER | None = None
    description: str | None = Field(
        default=None,
        max_length=DESCRIPTION_MAX_LEN,
    )
    photo_id: uuid.UUID | None = None
    managers_id: list[uuid.UUID] | None = None
    is_active: bool | None = None

    @field_validator(
        'name',
        'address',
        'phone',
        'managers_id',
        mode='before',
    )
    @classmethod
    def prevent_none(cls, value: Any, info: ValidationInfo) -> Any:
        """Запрещает передачу явного None (null) для обязательных полей."""
        if value is None:
            raise ValueError(f'Поле {info.field_name} не может быть null')
        return value


class CafeShortInfo(CafeBase):
    """Схема для краткого отображения заведения в списках и выпадающих меню."""

    id: uuid.UUID


class CafeInfo(CafeBase):
    """Полная схема кафе."""

    id: uuid.UUID
    managers: list['UserShortInfo']
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
