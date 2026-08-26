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

from src.cafes.schemas import CafeShortInfo
from src.core.constants import MIN_TABLE_CAPACITY


class TableBase(BaseModel):
    """Базовая схема стола."""

    description: str | None = None
    seat_number: int = Field(..., ge=MIN_TABLE_CAPACITY)


class TableInfo(TableBase):
    """Полная схема стола."""

    id: uuid.UUID
    cafe: CafeShortInfo
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TableShortInfo(TableBase):
    """Краткая схема стола."""

    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class TableCreate(TableBase):
    """Схема для создания нового стола."""


class TableUpdate(BaseModel):
    """Схема для частичного обновления стола."""

    description: str | None = None
    seat_number: int | None = Field(default=None, ge=MIN_TABLE_CAPACITY)
    is_active: bool | None = None

    @field_validator(
        'seat_number',
        'is_active',
        mode='before',
    )
    @classmethod
    def prevent_none(cls, value: Any, info: ValidationInfo) -> Any:
        """Запрещает передачу явного None (null) для обязательных полей."""
        if value is None:
            raise ValueError(f'Поле {info.field_name} не может быть null')
        return value
