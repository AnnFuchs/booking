from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.logger import get_logger
from src.users.errors import DuplicateInfoError
from src.users.schemas import AdminUserCreate
from src.users.service import user_service

logger = get_logger(__name__)


async def create_first_admin(
    session: AsyncSession,
    login: str = settings.first_superuser_login,
    password: str = settings.first_superuser_password,
) -> None:
    """Автоматизация создания первого админа."""
    existing_user = await user_service.get_user_by_login(session, login)
    if existing_user:
        logger.debug(
            'Администратор %s уже существует, создание не требуется.',
            login,
        )
        return

    try:
        if '@' in login:
            logger.debug('Логин определён как email: %s', login)
            await user_service.create(
                session,
                AdminUserCreate(
                    username='test_super',
                    email=login,
                    password=password,
                ),
            )
        else:
            logger.debug('Логин определён как номер телефона: %s', login)
            await user_service.create(
                session,
                AdminUserCreate(
                    username='test_super',
                    phone=login,
                    password=password,
                ),
            )
        logger.info('Первый администратор с логином %s создан.', login)
    except DuplicateInfoError as e:
        logger.debug(
            'Пользователь с переданным данными уже существует. Ошибки: %s',
            e.args,
        )
