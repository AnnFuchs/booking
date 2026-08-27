from datetime import datetime
from typing import Any, Self
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    ValidationInfo,
    field_validator,
    model_validator,
)

from src.core.constants import E164_RU_NUMBER, MIN_LEN, Role
from src.users.validators import (
    validate_password_value,
    validate_username_value,
)


class UserShortInfo(BaseModel):
    """Короткая pydantic-схема для просмотра пользователя."""

    id: UUID
    username: str = Field(..., min_length=MIN_LEN)
    phone: E164_RU_NUMBER | None = None
    email: EmailStr | None = None
    tg_id: str | None = None

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class UserInfo(UserShortInfo):
    """Pydantic-схема для просмотра пользователя."""

    role: Role
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    """Pydantic-схема для создания пользователя."""

    username: str = Field(..., min_length=MIN_LEN)
    email: EmailStr | None = None
    phone: E164_RU_NUMBER | None = None
    tg_id: str | None = None
    password: SecretStr

    @field_validator('username')
    @classmethod
    def validate_username(cls, value: str) -> str:
        """Валидация имени пользователя."""
        return validate_username_value(value=value)

    @field_validator('password', mode='after')
    @classmethod
    def validate_password(cls, value: SecretStr) -> SecretStr:
        """Валидация пароля."""
        return validate_password_value(value=value)

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


class UserUpdate(BaseModel):
    """Pydantic-схема для обновления пользователя."""

    username: str | None = Field(default=None, min_length=MIN_LEN)
    password: SecretStr | None = None
    email: EmailStr | None = None
    phone: E164_RU_NUMBER | None = None
    tg_id: str | None = None

    model_config = ConfigDict(from_attributes=True, extra='forbid')

    @field_validator('username')
    @classmethod
    def validate_username_if_present(cls, v: str | None) -> str | None:
        """Валидация имени пользователя."""
        if v is not None:
            return validate_username_value(v)
        return v

    @field_validator('password', mode='after')
    @classmethod
    def validate_password_if_present(
        cls,
        value: SecretStr | None,
    ) -> SecretStr | None:
        """Валидация пароля."""
        if value is not None:
            return validate_password_value(value)
        return value

    @field_validator(
        'username',
        'password',
        mode='before',
    )
    @classmethod
    def prevent_none(cls, value: Any, info: ValidationInfo) -> Any:
        """Запрещает передачу явного None (null) для обязательных полей."""
        if value is None:
            raise ValueError(f'Поле {info.field_name} не может быть null')
        return value


class UserUpdateAdmin(UserUpdate):
    """Pydantic-схема для обновления пользователя админом.

    Позволяет менять роль и деактивировать запись.
    """

    role: Role | None = None
    is_active: bool | None = None

    @field_validator(
        'username',
        'password',
        'is_active',
        mode='before',
    )
    @classmethod
    def prevent_none(cls, value: Any, info: ValidationInfo) -> Any:
        """Запрещает передачу явного None (null) для обязательных полей."""
        if value is None:
            raise ValueError(f'Поле {info.field_name} не может быть null')
        return value
