from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from src.core.config import settings
from src.core.logger import get_logger

engine = create_async_engine(settings.database_url)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

sync_engine = create_engine(settings.sync_database_url)
SessionLocal = sessionmaker(sync_engine, expire_on_commit=False)

logger = get_logger(__name__)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Генератор асинхронной сессии для базы данных."""
    async with AsyncSessionLocal() as async_session:
        logger.debug('Сессия БД открыта.')
        try:
            yield async_session
            await async_session.commit()
        except Exception as e:
            logger.error(
                'Ошибка транзакции в сессии БД: %s',
                e,
                exc_info=True,
            )
            await async_session.rollback()
            raise
        finally:
            await async_session.close()
        logger.debug('Сессия БД закрыта.')
