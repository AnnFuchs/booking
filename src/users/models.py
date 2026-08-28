import uuid
from typing import TYPE_CHECKING

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from src.core.constants import (
    EMAIL_MAX_LEN,
    PHONE_MAX_LEN,
    PW_MAX_LEN,
    TG_ID_MAX_LEN,
    USERNAME_MAX_LEN,
    Role,
)
from src.db.base import Base
from src.db.utils import validate_and_format_phone

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
    __table_args__ = (
        CheckConstraint(
            '(email IS NOT NULL) OR (phone IS NOT NULL)',
            name='email_or_phone_not_null',
        ),
        Index('ix_users_role_active', 'role', 'is_active'),
    )

    username: Mapped[str] = mapped_column(
        String(length=USERNAME_MAX_LEN),
        nullable=False,
        unique=True,
        index=True,
    )
    email: Mapped[str | None] = mapped_column(
        String(length=EMAIL_MAX_LEN),
        unique=True,
        index=True,
    )
    phone: Mapped[str | None] = mapped_column(
        String(length=PHONE_MAX_LEN),
        unique=True,
        index=True,
    )
    tg_id: Mapped[str | None] = mapped_column(
        String(length=TG_ID_MAX_LEN),
        unique=True,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(length=PW_MAX_LEN),
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
    cafe: Mapped['Cafe | None'] = relationship(
        'Cafe',
        back_populates='managers',
        lazy='noload',
    )

    @validates('phone')
    def validate_phone(self, key: str, phone: str | None) -> str | None:
        """Валидация номера телефона (обёртка над утилитой)."""
        if phone is None:
            return None
        return validate_and_format_phone(phone)

    @validates('email')
    def validate_email(self, key: str, email: str | None) -> str | None:
        """Валидация email."""
        if email is None:
            return None
        try:
            valid_email = validate_email(email, check_deliverability=False)
            return valid_email.normalized
        except EmailNotValidError:
            raise ValueError(
                'Переданное в поле email значение не является валидным '
                'адресом электронной почты.',
            )
