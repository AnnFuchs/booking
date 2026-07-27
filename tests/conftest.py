import asyncio
import sys
from collections.abc import AsyncGenerator, Generator

import pytest
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text

from src.core.config import settings
from src.main import app

# Переменные окружения из .env
env_path = settings.model_config.get('env_file')
load_dotenv(dotenv_path=env_path)


# --- ПЛАГИНЫ ---
pytest_plugins = [
    'tests.fixtures.db',
    'tests.fixtures.auth',
    'tests.fixtures.entities',
]


# --- СИСТЕМНЫЕ НАСТРОЙКИ ---
@pytest.fixture(scope='session')
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Создает экземпляр event loop для всей тестовой сессии."""
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# --- УПРАВЛЕНИЕ ТЕСТОВОЙ БД ---
@pytest.fixture(scope='session')
def manage_db() -> Generator[None, None, None]:
    """Создает физическую базу данных cafedbdev_test."""
    test_db_name = f'{settings.postgres_db}_test'
    root_url = (
        f'postgresql://{settings.postgres_user}:'
        f'{settings.postgres_password.get_secret_value()}'
        f'@{settings.postgres_server}:{settings.postgres_port}/postgres'
    )

    # Используем синхронный engine для админ-команд
    sync_engine = create_engine(root_url, isolation_level='AUTOCOMMIT')
    with sync_engine.connect() as conn:
        conn.execute(
            text(f'DROP DATABASE IF EXISTS {test_db_name} WITH (FORCE)'),
        )
        conn.execute(text(f'CREATE DATABASE {test_db_name}'))
    sync_engine.dispose()
    yield
    # После всех тестов базу можно не удалять для дебага,
    # либо добавить DROP здесь.


# --- КЛИЕНТ ДЛЯ API ---
@pytest.fixture(scope='session')
async def async_client(manage_db: None) -> AsyncGenerator[AsyncClient, None]:
    """Инициализирует асинхронный клиент HTTPX для тестирования эндпоинтов.

    base_url должен совпадать с префиксом в OpenAPI (например, /api/v1).
    """
    # Префикс, только здесь здесь
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test/api/v1',
    ) as ac:
        yield ac
