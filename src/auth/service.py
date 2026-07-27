from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.password import verify_password
from src.core.logger import get_logger
from src.users.models import User
from src.users.service import user_service

logger = get_logger(__name__)


class AuthService:
    """Сервис-класс для аутентификации."""

    async def auth_by_login(
        self,
        login: str,
        password: SecretStr,
        session: AsyncSession,
    ) -> User | None:
        """Аутентификация пользователей."""
        user = await user_service.get_user_by_login(session, login)

        if not user:
            logger.warning(
                'Пользователь не найден при аутентификации: %s',
                login,
            )
            return None

        if not verify_password(
            plain_password=password.get_secret_value(),
            hashed_password=user.hashed_password,
        ):
            logger.warning('Неверный пароль при аутентификации: %s', login)
            return None

        logger.debug('Аутентификация успешна: %s', login)
        return user


auth_service = AuthService()
