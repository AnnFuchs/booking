from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from src.bookings.utils import validate_date_not_in_past
from src.core.constants import MAX_BOOKING_COMMENT, BookingStatus
from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models_for_alembic import Cafe, Slot, Table, User


class Booking(Base):
    """Модель для хранения информации о бронированиях столов."""

    __tablename__ = 'bookings'
    __table_args__ = (
        CheckConstraint(
            'guest_number > 0',
            name='check_booking_guest_number_positive',
        ),
        Index('ix_bookings_user_id', 'user_id'),
        Index('ix_bookings_user_date', 'user_id', 'booking_date'),
        Index('ix_bookings_status_active', 'status', 'is_active'),
        Index(
            'ix_bookings_cafe_date_active',
            'cafe_id',
            'booking_date',
            'is_active',
        ),
        Index(
            'ix_bookings_date_status_active',
            'booking_date',
            'status',
            'is_active',
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey('users.id'),
        nullable=False,
    )

    guest_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    note: Mapped[str | None] = mapped_column(String(MAX_BOOKING_COMMENT))
    status: Mapped[BookingStatus] = mapped_column(
        default=BookingStatus.BOOKING,
        nullable=False,
    )

    tables_slots: Mapped[list['TableSlot']] = relationship(
        'TableSlot',
        back_populates='booking',
        lazy='selectin',
    )
    cafe_id: Mapped[UUID] = mapped_column(
        ForeignKey('cafes.id'),
        nullable=False,
        index=True,
    )

    booking_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    @validates('booking_date')
    def validate_booking_date(self, key: str, value: date) -> date:
        """Проверяет дату на валидность."""
        return validate_date_not_in_past(value)

    cafe: Mapped['Cafe'] = relationship(
        'Cafe',
        backref='bookings',
        lazy='selectin',
    )

    user: Mapped['User'] = relationship(
        'User',
        backref='bookings',
        lazy='selectin',
    )


class TableSlot(Base):
    """Связка конкретного стола и временного интервала."""

    __tablename__ = 'table_slots'
    __table_args__ = (
        UniqueConstraint(
            'table_id',
            'slot_id',
            'booking_date',
            name='uq_table_slot_date',
        ),
        Index('ix_table_slots_table_date', 'table_id', 'booking_date'),
        Index('ix_table_slots_slot_date', 'slot_id', 'booking_date'),
        Index('ix_table_slots_booking_id', 'booking_id'),
        Index('ix_table_slots_date_active', 'booking_date', 'is_active'),
        Index(
            'ix_table_slots_date_active_booking',
            'booking_date',
            'is_active',
            'booking_id',
        ),
    )

    table_id: Mapped[UUID] = mapped_column(
        ForeignKey('tables.id', ondelete='CASCADE'),
    )
    slot_id: Mapped[UUID] = mapped_column(
        ForeignKey('slots.id', ondelete='CASCADE'),
    )
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)

    booking_id: Mapped[UUID | None] = mapped_column(
        ForeignKey('bookings.id', ondelete='SET NULL'),
        nullable=True,
    )
    booking: Mapped['Booking | None'] = relationship(
        'Booking',
        back_populates='tables_slots',
        lazy='selectin',
    )

    table: Mapped['Table'] = relationship(
        'Table',
        backref='table_slots',
        lazy='selectin',
    )
    slot: Mapped['Slot'] = relationship(
        'Slot',
        backref='table_slots',
        lazy='selectin',
    )
