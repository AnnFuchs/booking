from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.core.config import settings
from src.db.base import Base
from src.db.session import get_async_session
from src.main import app

TEST_DATABASE_URL = settings.database_url + '_test'


engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture(scope='session')
async def engine(manage_db: None) -> AsyncGenerator:
    """Создает асинхронный движок для тестов."""
    _engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    yield _engine
    await _engine.dispose()


@pytest.fixture(scope='session', autouse=True)
async def setup_db(
    engine: AsyncEngine,
) -> AsyncGenerator:
    """Создает таблицы в уже существующей базе."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Обеспечивает чистую сессию для каждого теста."""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture(autouse=True)
async def override_db(session: AsyncSession) -> AsyncGenerator[None, None]:
    """Подменяет зависимость БД в FastAPI приложении."""

    async def _get_test_db() -> AsyncGenerator[AsyncSession, None]:
        yield session

    app.dependency_overrides[get_async_session] = _get_test_db
    yield
    app.dependency_overrides.clear()
