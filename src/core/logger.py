import logging
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler

from src.core.constants import (
    LOG_BACKUP_COUNT,
    LOG_DATEFMT,
    LOG_FILE_PATH,
    LOG_FORMAT,
    LOG_MAX_BYTES,
    LOG_SYS_NAME,
)

_user_info_ctx: ContextVar[str] = ContextVar('user_info', default=LOG_SYS_NAME)


def set_user_context(
    username: str | None = None,
    user_id: str | None = None,
) -> None:
    """Установка контекста пользователя для текущего запроса."""
    if username and user_id:
        user_info = f'{username}({user_id})'
    else:
        user_info = LOG_SYS_NAME
    _user_info_ctx.set(user_info)


def reset_user_context() -> None:
    """Сброс контекста пользователя после запроса."""
    _user_info_ctx.set(LOG_SYS_NAME)


class UserContextFilter(logging.Filter):
    """Добавление информации о пользователе в логи."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Подстановка информации о пользователе в логе."""
        record.user_info = _user_info_ctx.get()
        return True


def _configure_logger(logger: logging.Logger) -> None:
    """Применяет единый форматтер, хендлеры и фильтр к логгеру."""
    logger.setLevel(logging.INFO)
    logger.addFilter(UserContextFilter())
    logger.propagate = False

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATEFMT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        LOG_FILE_PATH,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8',
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Настройка логирования."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        _configure_logger(logger)
    return logger


def setup_logging() -> None:
    """Настройка корневого логирования для всего приложения."""
    for uvicorn_logger_name in ('uvicorn', 'uvicorn.error', 'uvicorn.access'):
        uvicorn_logger = logging.getLogger(uvicorn_logger_name)
        uvicorn_logger.handlers = []
        _configure_logger(uvicorn_logger)
