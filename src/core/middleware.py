from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.core.logger import get_logger, reset_user_context

logger = get_logger(__name__)


class ResetUserContextMiddleware(BaseHTTPMiddleware):
    """Сброс контекста пользователя после каждого запроса."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Сброс контекста пользователя до SYSTEM после обработки запроса."""
        try:
            return await call_next(request)
        except Exception as e:
            logger.error('Ошибка в ResetUserContextMiddleware: %s', e)
            raise
        finally:
            try:
                reset_user_context()
            except Exception as e:
                logger.error('Ошибка сброса контекста пользователя: %s', e)
