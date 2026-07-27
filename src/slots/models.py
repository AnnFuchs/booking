import uuid
from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Text
from sqlalchemy import Time as SQLTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.constants import TIME_FORMAT
from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models_for_alembic import Cafe
# if TYPE_CHECKING:
# from src.cafes.models import Cafe


class Slot(Base):
    """Модель временного слота.

    Атрибуты:
        start_time: Время начала слота
        end_time: Время окончания слота
        description: Описание слота
        cafe_id: ID кафе
        cafe: Связь с моделью Cafe

    Валидации:
        - start_time должно быть меньше end_time
        - Для одного кафе не может быть пересекающихся слотов
    """

    __tablename__ = 'slots'
    __table_args__ = (
        CheckConstraint('start_time < end_time', name='check_time_order'),
        Index('ix_slots_cafe_active', 'cafe_id', 'is_active'),
        Index('ix_slots_cafe_start_time', 'cafe_id', 'start_time'),
    )
    start_time: Mapped[time] = mapped_column(
        SQLTime(timezone=False),
        nullable=False,
    )
    end_time: Mapped[time] = mapped_column(
        SQLTime(timezone=False),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
    )
    cafe_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey('cafes.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    cafe: Mapped['Cafe'] = relationship(
        'Cafe',
        back_populates='slots',
        lazy='selectin',
    )

    def __repr__(self) -> str:
        """Строковое представление слота для отладки."""
        slots_fields = [
            f'Slot_ID={self.id}',
            f'cafe={self.cafe_id}',
            f'start_time={self.start_time.strftime(TIME_FORMAT)}',
            f'end_time={self.end_time.strftime(TIME_FORMAT)}',
            f'is_active={self.is_active}',
        ]
        return ', '.join(slots_fields)
