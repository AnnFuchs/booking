from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    ValidationInfo,
    field_validator,
)

from src.cafes.schemas import CafeShortInfo
from src.core.constants import MAX_BOOKING_COMMENT
from src.slots.schemas import TimeSlotShortInfo
from src.tables.schemas import TableShortInfo
from src.users.schemas import UserShortInfo


class BookingTableSlot(BaseModel):
    """Схема для пары стол-слот при бронировании."""

    table_id: UUID
    slot_id: UUID


class BookingTableSlotShortInfo(BaseModel):
    """Схема для вложенного списка tables_slots."""

    table: TableShortInfo
    slot: TimeSlotShortInfo


class BookingCreate(BaseModel):
    """Схема для создания бронирования."""

    cafe_id: UUID
    tables_slots: list[BookingTableSlot] = Field(..., min_length=1)
    guest_number: int = Field(..., gt=0)
    note: str | None = Field(None, max_length=MAX_BOOKING_COMMENT)
    booking_date: date

    @field_validator('booking_date')
    @classmethod
    def validate_booking_date(cls, v: date) -> date:
        """Проверяет дату на валидность."""
        if v < date.today():
            raise ValueError('Дата бронирования не может быть в прошлом')
        return v


class BookingInfo(BaseModel):
    """Схема для ответа API."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    user: UserShortInfo
    cafe: CafeShortInfo
    tables_slots: list[BookingTableSlotShortInfo]
    guest_number: int
    note: str | None = None
    status: 'BookingStatus'
    booking_date: date
    is_active: bool
    created_at: datetime
    updated_at: datetime


class BookingStatus(RootModel):
    """Статусы бронирования."""

    root: str = Field(..., description='Статусы бронирования')

    model_config = ConfigDict(
        json_schema_extra={
            'type': 'string',
            'oneOf': [
                {
                    'const': 'BOOKING',
                    'title': 'Booking',
                    'description': 'Забронировано',
                },
                {
                    'const': 'CANCELED',
                    'title': 'Canceled',
                    'description': 'Отменено',
                },
                {
                    'const': 'ACTIVE',
                    'title': 'Active',
                    'description': 'Клиент подошел',
                },
                {
                    'const': 'COMPLETED',
                    'title': 'Completed',
                    'description': 'Обслуживание завершено',
                },
            ],
        },
    )


class BookingUpdate(BaseModel):
    """Схема для обновления бронирования."""

    tables_slots: list[BookingTableSlot] | None = Field(None, min_length=1)
    guest_number: int | None = Field(None, gt=0)
    note: str | None = Field(None, max_length=MAX_BOOKING_COMMENT)
    status: BookingStatus | None = None
    booking_date: date | None = None
    is_active: bool | None = None

    @field_validator(
        'tables_slots',
        'guest_number',
        'status',
        'booking_date',
        'is_active',
        mode='before',
    )
    @classmethod
    def prevent_none(cls, value: Any, info: ValidationInfo) -> Any:
        """Запрещает передачу явного None (null) для обязательных полей."""
        if value is None:
            raise ValueError(f'Поле {info.field_name} не может быть null')
        return value

    @field_validator('booking_date')
    @classmethod
    def validate_date(cls, value: date | None) -> date | None:
        """Проверяет, что дата бронирования не находится в прошлом."""
        if value is not None and value < date.today():
            raise ValueError('Дата бронирования не может быть в прошлом')
        return value
