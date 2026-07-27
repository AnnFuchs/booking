from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.logger import get_logger, setup_logging
from src.core.middleware import ResetUserContextMiddleware
from src.core.router import main_router
from src.db.first_admin import create_first_admin
from src.db.models_for_alembic import Base  # noqa
from src.db.session import AsyncSessionLocal

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Создание админа на старте приложения."""
    logger.info('Запуск приложения...')
    async with AsyncSessionLocal() as session:
        await create_first_admin(session=session)
    logger.info('Приложение запущено.')
    yield
    logger.info('Приложение завершает работу.')


app = FastAPI(
    title=settings.app_title,
    description=settings.app_description,
    servers=settings.app_servers,
    lifespan=lifespan,
    root_path='/api/v1',
)

app.add_middleware(ResetUserContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(main_router)
