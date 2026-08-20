import uuid
from datetime import datetime, time
from typing import Any, Optional, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)

from src.cafes.schemas import CafeShortInfo
from src.slots.utils import validate_slot_time


class TimeValidationBase(BaseModel):
    """Базовый класс для слота с валидацией времени."""

    start_time: time = Field(..., description='Время начала слота')
    end_time: time = Field(..., description='Время окончания слота')

    @model_validator(mode='after')
    def check_time_order_if_both_provided(self) -> Self:
        """Проверка порядка времени, если в запросе переданы ОБА поля.

        Это защищает от некорректных запросов вида {start: 20:00, end: 10:00}.
        """
        if self.start_time is not None and self.end_time is not None:
            validate_slot_time(self.start_time, self.end_time)
        return self


class TimeSlotCreate(TimeValidationBase):
    """Схема для создания временного слота.

    Используется в POST /cafes/{cafe_id}/time_slots
    """

    description: Optional[str] = Field(None, description='Описание слота')
    model_config = ConfigDict(
        extra='forbid',
        json_schema_extra={
            'example': {
                'start_time': '10:00:00',
                'end_time': '12:00:00',
                'description': 'время завтрака',
            },
        },
    )


class TimeSlotShortInfo(BaseModel):
    """Краткая информация о временном слоте.

    Используется внутри BookingInfo.
    """

    id: uuid.UUID = Field(..., description='ID слота')
    start_time: time = Field(..., description='Время начала слота')
    end_time: time = Field(..., description='Время окончания слота')
    description: Optional[str] = Field(None, description='Описание слота')

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            'example': {
                'id': '550e8400-e29b-41d4-a716-446655440000',
                'start_time': '10:00:00',
                'end_time': '12:00:00',
                'description': 'Утренний слот',
            },
        },
    )


class TimeSlotInfo(BaseModel):
    """Полная информация о временном слоте.

    Используется:
    GET /cafes/{cafe_id}/time_slots
    GET /cafes/{cafe_id}/time_slots/{slot_id}
    """

    id: uuid.UUID = Field(..., description='ID слота')
    cafe: CafeShortInfo = Field(..., description='Информация о кафе')
    start_time: time = Field(..., description='Время начала слота')
    end_time: time = Field(..., description='Время окончания слота')
    description: Optional[str] = Field(None, description='Описание слота')
    is_active: bool = Field(..., description='Активен ли слот')
    created_at: datetime = Field(..., description='Дата создания')
    updated_at: datetime = Field(..., description='Дата обновления')

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            'example': {
                'id': '550e8400-e29b-41d4-a716-446655440000',
                'cafe': {
                    'id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                    'name': 'string',
                    'address': 'string',
                    'phone': 'string',
                    'description': 'string',
                    'photo_id': '6ba7b810-9dad-11d1-80b4-00c04fd430c8',
                },
                'start_time': '10:00:00',
                'end_time': '12:00:00',
                'description': 'string',
                'is_active': True,
                'created_at': '2026-01-01T10:00:00',
                'updated_at': '2026-01-01T10:00:00',
            },
        },
    )


class TimeSlotUpdate(TimeValidationBase):
    """Схема для обновления временного слота.

    Используется в PATCH /cafes/{cafe_id}/time_slots/{slot_id}
    """

    start_time: Optional[time] = Field(None, description='Время начала слота')
    end_time: Optional[time] = Field(None, description='Время окончания слота')
    description: Optional[str] = Field(None, description='Описание слота')
    is_active: Optional[bool] = Field(None, description='Активен ли слот')

    @field_validator(
        'start_time',
        'end_time',
        'is_active',
        mode='before',
    )
    @classmethod
    def prevent_none(cls, value: Any, info: ValidationInfo) -> Any:
        """Запрещает передачу явного None (null) для обязательных полей."""
        if value is None:
            raise ValueError(f'Поле {info.field_name} не может быть null')
        return value
