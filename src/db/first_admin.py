from email_validator import EmailNotValidError, validate_email
from phonenumbers import (
    NumberParseException,
    PhoneNumberFormat,
    format_number,
    is_valid_number,
)
from phonenumbers import parse as phone_parse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.logger import get_logger
from src.users.errors import DuplicateInfoError
from src.users.schemas import AdminUserCreate
from src.users.service import user_service

logger = get_logger(__name__)


def _normalize_login(login: str) -> tuple[str | None, str | None, str | None]:
    """Нормализация переданного логина.

    Если логин email, также возвращает local part.
    """
    try:
        email_login = validate_email(login)
        return email_login.normalized, 'email', email_login.local_part
    except EmailNotValidError:
        try:
            parsed_phone = phone_parse(login, 'RU')
            if is_valid_number(parsed_phone):
                normalized = format_number(
                    parsed_phone,
                    PhoneNumberFormat.E164,
                )
                return normalized, 'phone', None
        except NumberParseException:
            pass

    return None, None, None


async def create_first_admin(
    session: AsyncSession,
    login: str = settings.first_superuser_login,
    password: str = settings.first_superuser_password,
) -> None:
    """Автоматизация создания первого админа."""
    normalized_login, login_type, local_part = _normalize_login(login)

    if not normalized_login or not login_type:
        logger.error(
            'Логин не является ни валидным email, '
            'ни валидным номером телефона: %s',
            login,
        )
        raise RuntimeError(
            'Ошибка при создании первого суперпользователя, не валиден логин.',
        )

    existing_user = await user_service.get_user_by_login(
        session,
        normalized_login,
    )
    if existing_user:
        logger.debug(
            'Администратор %s уже существует, создание не требуется.',
            normalized_login,
        )
        return

    try:
        if login_type == 'email':
            await user_service.create(
                session,
                AdminUserCreate(
                    username=local_part,
                    email=normalized_login,
                    password=password,
                ),
            )
        else:
            await user_service.create(
                session,
                AdminUserCreate(
                    username=f'user_{normalized_login}',
                    phone=normalized_login,
                    password=password,
                ),
            )
        logger.info('Первый администратор %s создан.', normalized_login)
    except DuplicateInfoError as e:
        logger.debug('Пользователь уже существует: %s', e.args)
