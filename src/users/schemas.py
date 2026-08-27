import re
from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)

from src.core.constants import E164_RU_NUMBER, MIN_LEN, Role


class PhoneValidatorMixin(BaseModel):
    """Mixin для валидации номера телефона."""

    phone: E164_RU_NUMBER | None = None

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Валидация номера телефона."""
        if v is None:
            return v
        v = str(v)
        if not v.startswith('+7'):
            raise ValueError('Номер телефона должен начинаться с +7')
        if len(v) != 12:
            raise ValueError('Номер телефона должен содержать 12 символов')
        return v


class UserShortInfo(PhoneValidatorMixin):
    """Короткая pydantic-схема для просмотра пользователя."""

    id: UUID
    username: str = Field(..., min_length=MIN_LEN)
    email: EmailStr | None = None
    tg_id: str | None = None

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class UserInfo(UserShortInfo):
    """Pydantic-схема для просмотра пользователя."""

    role: Role
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserCreate(PhoneValidatorMixin):
    """Pydantic-схема для создания пользователя."""

    username: str = Field(..., min_length=MIN_LEN)
    email: EmailStr | None = None
    tg_id: str | None = None
    password: SecretStr

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Валидация имени пользователя."""
        if not v or not v.strip():
            raise ValueError(
                'Имя пользователя не может быть пустым '
                'или состоять только из пробелов.',
            )
        return v.strip()

    @field_validator('password', mode='after')
    @classmethod
    def validate_password(cls, value: SecretStr) -> SecretStr:
        """Check password is secure."""
        pwd = value.get_secret_value()
        pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d).{8,}$'
        if not re.fullmatch(pattern, pwd):
            raise ValueError(
                'Пароль должен содержать не менее 8 знаков, ',
                'включая 1 заглавную латинскую букву, ',
                '1 прописную латинскую букву и 1 цифру.',
            )
        return value

    @model_validator(mode='after')
    def validate_contacts(self) -> Self:
        """Проверка наличия email или телефона.

        В случае отсутствия обоих полей вызывает ValueError.
        """
        if not self.email and not self.phone:
            raise ValueError('Укажите email или телефон.')
        return self

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class AdminUserCreate(UserCreate):
    """Pydantic-схема для создания админа."""

    role: Role = Role.ADMIN


class UserUpdate(PhoneValidatorMixin):
    """Pydantic-схема для обновления пользователя."""

    username: str | None = Field(default=None, min_length=MIN_LEN)
    email: EmailStr | None = None
    tg_id: str | None = None
    password: SecretStr | None = None

    model_config = ConfigDict(from_attributes=True, extra='forbid')

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str | None) -> str | None:
        """Валидация имени пользователя."""
        if v is not None and not v.strip():
            raise ValueError(
                'Имя пользователя не может быть пустым '
                'или состоять только из пробелов.',
            )
        return v.strip() if v else v

    @field_validator('password', mode='after')
    @classmethod
    def validate_password(cls, value: SecretStr | None) -> SecretStr:
        """Check password is secure."""
        if value is None:
            raise ValueError('Пароль не может быть null.')
        pwd = value.get_secret_value()
        pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d).{8,}$'
        if not re.fullmatch(pattern, pwd):
            raise ValueError(
                'Пароль должен содержать не менее 8 знаков, ',
                'включая 1 заглавную латинскую букву, ',
                '1 прописную латинскую букву и 1 цифру.',
            )
        return value


class UserUpdateAdmin(UserUpdate):
    """Pydantic-схема для обновления пользователя админом.

    Позволяет менять роль и деактивировать запись.
    """

    role: Role | None = None
    is_active: bool | None = None
