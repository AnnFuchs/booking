import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.cafes.schemas import CafeShortInfo


class TableBase(BaseModel):
    """Базовая схема стола."""

    description: str | None = None
    seat_number: int = Field(..., ge=1)


class TableCreate(TableBase):
    """Схема для создания нового стола."""


class TableUpdate(BaseModel):
    """Схема для частичного обновления стола."""

    description: str | None = None
    seat_number: int | None = Field(default=None, ge=1)
    is_active: bool | None = None


class TableInfo(BaseModel):
    """Полная схема стола."""

    id: uuid.UUID
    cafe: CafeShortInfo
    description: str | None
    seat_number: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TableShortInfo(BaseModel):
    """Заглушка."""

    id: uuid.UUID
    description: str | None = None
    seat_number: int = Field(None, alias='seat_number')

    model_config = ConfigDict(populate_by_name=True)
