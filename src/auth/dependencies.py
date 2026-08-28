from typing import Annotated, Callable, Sequence
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.constants import (
    TOKEN_FORMAT,
    TOKEN_TYPE,
    Role,
)
from src.core.logger import get_logger, set_user_context
from src.db.session import get_async_session
from src.users.models import User

security = HTTPBearer(
    bearerFormat=TOKEN_FORMAT,
    scheme_name=TOKEN_TYPE,
    auto_error=False,
)

logger = get_logger(__name__)


async def get_current_user_optional(
    session: AsyncSession = Depends(get_async_session),
    credentials: HTTPAuthorizationCredentials | None = Depends(
        security,
    ),
) -> User | None:
    """Получение текущего пользователя или None.

    Позволяет открыть доступ для анонима ИЛИ пользователя.
    Для пользователя в дальнейшем предполагается проверка ролей.
    """
    if not credentials:
        return None

    try:
        auth_data = settings.jwt_auth_data
        payload = jwt.decode(
            credentials.credentials,
            auth_data['secret_key'],
            algorithms=[auth_data['algorithm']],
        )
    except ExpiredSignatureError:
        logger.warning('Попытка авторизации с истекшим токеном.')
        return None
    except JWTError:
        logger.warning('Ошибка JWT.')
        return None

    sub = payload.get('sub')
    if not sub:
        logger.warning('Subject не найден в JWT payload.')
        return None

    try:
        uuid_sub = UUID(sub)
    except (ValueError, TypeError, AttributeError):
        logger.warning('Subject невозможно трансформировать в UUID.')
        return None

    user = await session.get(User, uuid_sub)
    if not user:
        logger.warning('Пользователь с переданным id не найден.')
        return None

    if not user.is_active:
        logger.warning('Пользователь с переданным id деактивирован.')
        return None

    set_user_context(username=user.username, user_id=str(user.id))
    return user


def get_user_by_role(
    required_roles: Sequence[Role],
    *,
    allow_anon: bool = False,
) -> Callable:
    """Фабрика зависимости для проверки роли пользователя.

    - allow_anon=False (по умолчанию) - только авторизованные
    - allow_anon=True - аноним ИЛИ пользователь с ролью
    """

    async def role_checker(
        user: Annotated[User | None, Depends(get_current_user_optional)],
    ) -> User:
        if user is None:
            if allow_anon:
                logger.debug('Доступ анонимному пользователю разрешен.')
                return None
            logger.warning('Доступ без авторизации запрещен.')
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Необходима авторизация',
            )
        if user and user.role not in required_roles:
            logger.warning('Недостаточно прав для выполнения операции.')
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Недостаточно прав для выполнения операции.',
            )
        logger.debug('Проверка доступа прошла успешно')
        return user

    return role_checker
