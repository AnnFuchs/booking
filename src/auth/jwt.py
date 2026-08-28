from datetime import datetime, timedelta, timezone

from jose import jwt

from src.core.config import settings
from src.core.constants import JWT_LIFE
from src.core.logger import get_logger

logger = get_logger(__name__)


def create_access_token(data: dict) -> str:
    """Генерация JWT токена."""
    if not data or 'sub' not in data:
        logger.warning(
            'Не переданы данные для создания токена или отсутствует sub.',
        )
        raise ValueError('Subject (sub) обязателен для создания токена')
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(seconds=JWT_LIFE)
    to_encode.update({'exp': expire})
    auth_data = settings.jwt_auth_data
    encoded = jwt.encode(
        to_encode,
        auth_data['secret_key'],
        algorithm=auth_data['algorithm'],
    )
    logger.debug('JWT токен успешно сгенерирован')
    return encoded
