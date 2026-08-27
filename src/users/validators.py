import re
from uuid import UUID

from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import get_logger
from src.db.utils import get_by_id_or_404
from src.users.crud import user_crud
from src.users.errors import DuplicateInfoError
from src.users.models import User

logger = get_logger(__name__)


def validate_username_value(value: str) -> str:
    """Валидация имени пользователя."""
    if not value or not value.strip():
        raise ValueError(
            'Имя пользователя не может быть пустым '
            'или состоять только из пробелов.',
        )
    return value.strip()


def validate_password_value(value: SecretStr) -> SecretStr:
    """Валидация безопасности пароля."""
    pwd = value.get_secret_value()
    pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d).{8,72}$'
    if not re.fullmatch(pattern, pwd):
        raise ValueError(
            'Пароль должен содержать не менее 8, но не более 72 знаков, '
            'включая 1 заглавную латинскую букву, '
            '1 прописную латинскую букву и 1 цифру.',
        )
    return value


async def check_user_exists(user_id: UUID, session: AsyncSession) -> User:
    """Проверяет, существует ли такой пользователь."""
    return await get_by_id_or_404(
        session,
        User,
        user_id,
        detail='Пользователь не найден',
        log_msg=f'Пользователь с id {user_id} не найден',
    )


async def check_user_data_duplicate(
    username: str | None,
    email: str | None,
    phone: str | None,
    session: AsyncSession,
    tg_id: str | None = None,
    exclude_id: UUID | None = None,
) -> None:
    """Проверяет, нет ли в базе данных пользователя с переданными данными."""
    checks = [
        ('username', username, 'Имя пользователя занято.'),
        ('email', email, 'Пользователь с таким email уже зарегистрирован.'),
        (
            'phone',
            phone,
            'Пользователь с таким номером телефона уже зарегистрирован.',
        ),
        ('tg_id', tg_id, 'Пользователь с таким tg_id уже зарегистрирован.'),
    ]

    filters = {field: val for field, val, _ in checks if val is not None}
    if not filters:
        logger.debug(
            'Среди переданных данных нет информации, '
            'требующей проверки на уникальность.',
        )
        return

    user = await user_crud.get_by_any_attribute(session, filters, exclude_id)

    if user:
        errors = [
            msg
            for field, val, msg in checks
            if val is not None and getattr(user, field) == val
        ]
        logger.warning(
            'При проверки данных на уникальность найдены ошибки: %s',
            errors,
        )
        raise DuplicateInfoError(*errors)
