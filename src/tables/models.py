import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.constants import DESCRIPTION_MAX_LEN
from src.db.base import Base
from src.db.models_for_alembic import Cafe


class Table(Base):
    """ORM модель стола."""

    __tablename__ = 'tables'
    __table_args__ = (
        CheckConstraint(
            'seat_number > 0',
            name='check_table_seat_number_positive',
        ),
        Index('ix_tables_cafe_id', 'cafe_id'),
        Index('ix_tables_cafe_active', 'cafe_id', 'is_active'),
        Index('ix_tables_seat_number', 'seat_number'),
        Index(
            'ix_tables_cafe_seats_active',
            'cafe_id',
            'seat_number',
            'is_active',
        ),
    )

    description: Mapped[str | None] = mapped_column(
        String(DESCRIPTION_MAX_LEN),
        nullable=True,
    )
    seat_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    cafe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('cafes.id'),
        nullable=False,
    )
    cafe: Mapped['Cafe'] = relationship(
        'Cafe',
        back_populates='tables',
        lazy='selectin',
    )
