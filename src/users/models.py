import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.constants import Role
from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models_for_alembic import Cafe


class User(Base):
    """Класс пользователя.

    Аттрибуты:
        id - UUID, унаследовано из класса Base
        username - str
        email - str | None
        phone - str| None
        tg_id - str| None
        hashed_password - str
        is_active - bool
        role - Role(StrEnum)
        created_at - datetime, унаследовано из класса Base
        updated_at - datetime, унаследовано из класса Base
        is_active - bool, унаследовано из класса Base
    """

    __tablename__ = 'users'

    username: Mapped[str] = mapped_column(
        String,
        nullable=False,
        unique=True,
        index=True,
    )
    email: Mapped[str | None] = mapped_column(
        String,
        unique=True,
        index=True,
    )
    phone: Mapped[str | None] = mapped_column(
        String,
        unique=True,
        index=True,
    )
    tg_id: Mapped[str | None] = mapped_column(
        String,
        unique=True,
    )
    hashed_password: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    role: Mapped[Role] = mapped_column(
        Enum(Role, name='role_enum'),
        default=Role.USER,
        nullable=False,
    )
    cafe_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('cafes.id', ondelete='SET NULL'),
        index=True,
    )
    cafe: Mapped['Cafe'] = relationship(
        'Cafe',
        back_populates='managers',
        lazy='selectin',
    )
    __table_args__ = (
        CheckConstraint(
            '(email IS NOT NULL) OR (phone IS NOT NULL)',
            name='email_or_phone_not_null',
        ),
    )
