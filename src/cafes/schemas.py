import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.cafes.validators import validate_managers_id
from src.core.constants import (
    ADDRESS_MAX_LENGTH,
    DESCRIPTION_MAX_LENGTH,
    E164_RU_NUMBER,
    MIN_LENGTH,
    NAME_MAX_LENGTH,
)
from src.users.schemas import UserShortInfo


class CafeBase(BaseModel):
    """Базовая схема кафе."""

    name: str = Field(
        min_length=MIN_LENGTH,
        max_length=NAME_MAX_LENGTH,
    )
    address: str = Field(
        min_length=MIN_LENGTH,
        max_length=ADDRESS_MAX_LENGTH,
    )
    phone: E164_RU_NUMBER
    description: str | None = Field(
        None,
        max_length=DESCRIPTION_MAX_LENGTH,
    )
    photo_id: uuid.UUID | None = None

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Валидация номера телефона."""
        v = str(v)
        if not v.startswith('+7'):
            raise ValueError('Номер телефона должен начинаться с +7')
        if len(v) != 12:
            raise ValueError('Номер телефона должен содержать 12 символов')
        return v


class CafeCreate(CafeBase):
    """Схема для создания нового кафе."""

    managers_id: list[uuid.UUID]

    _validate_managers_id = field_validator('managers_id')(
        validate_managers_id,
    )


class CafeUpdate(BaseModel):
    """Схема для частичного обновления кафе."""

    name: str | None = Field(
        default=None,
        max_length=NAME_MAX_LENGTH,
    )
    address: str | None = Field(
        default=None,
        max_length=ADDRESS_MAX_LENGTH,
    )
    phone: E164_RU_NUMBER | None = None
    description: str | None = Field(
        default=None,
        max_length=DESCRIPTION_MAX_LENGTH,
    )
    photo_id: uuid.UUID | None = None
    managers_id: list[uuid.UUID] | None = None
    is_active: bool | None = None

    _validate_managers_id = field_validator('managers_id')(
        validate_managers_id,
    )

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Валидация номера телефона."""
        if v is None:
            return v
        v = str(v)
        if not v.startswith('+7'):
            raise ValueError('Номер телефона должен начинаться с +7')
        if len(v) != 12:
            raise ValueError('Номер телефона должен содержать 12 символов')
        return v


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
