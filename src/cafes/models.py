from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from src.core.constants import (
    ADDRESS_MAX_LEN,
    DESCRIPTION_MAX_LEN,
    NAME_MAX_LEN,
    PHONE_MAX_LEN,
)
from src.db.base import Base
from src.db.utils import validate_and_format_phone

if TYPE_CHECKING:
    from src.db.models_for_alembic import Slot, Table, User


class Cafe(Base):
    """ORM модель кафе."""

    __tablename__ = 'cafes'

    __table_args__ = (
        UniqueConstraint('name', 'address', name='uq_cafe_name_address'),
    )

    name: Mapped[str] = mapped_column(
        String(NAME_MAX_LEN),
        nullable=False,
    )
    address: Mapped[str] = mapped_column(
        String(ADDRESS_MAX_LEN),
        nullable=False,
    )
    phone: Mapped[str] = mapped_column(
        String(PHONE_MAX_LEN),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(DESCRIPTION_MAX_LEN),
        nullable=True,
    )
    photo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('media.id', ondelete='SET NULL'),
        nullable=True,
    )
    tables: Mapped[list['Table']] = relationship(
        'Table',
        back_populates='cafe',
        lazy='selectin',
    )
    managers: Mapped[list['User']] = relationship(
        'User',
        back_populates='cafe',
        lazy='selectin',
    )
    slots: Mapped[list['Slot']] = relationship(
        'Slot',
        back_populates='cafe',
        cascade='all, delete-orphan',
        lazy='selectin',
    )

    @validates('phone')
    def validate_phone(self, key: str, phone: str) -> str:
        """Валидация номера телефона (обёртка над утилитой)."""
        return validate_and_format_phone(phone)

    def __repr__(self) -> str:
        """Строковое представление кафе для отладки."""
        cafe_fields = [
            f'Cafe_ID={self.id}',
            f'name="{self.name}"',
            f'address="{self.address}"',
            f'phone="{self.phone}"',
            f'is_active={self.is_active}',
        ]
        return ', '.join(cafe_fields)
