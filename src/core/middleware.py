from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.core.logger import reset_user_context


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
        finally:
            reset_user_context()
