import uuid
from typing import Any, Awaitable, Callable

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt import create_access_token
from src.core.constants import Role
from src.db.models_for_alembic import Cafe, User


@pytest.fixture
def create_user(session: AsyncSession) -> Callable[..., Awaitable[User]]:
    """Фабрика пользователей."""

    async def _create_user(
        role: Role = Role.USER,
        cafe_id: Any | None = None,
    ) -> User:
        user = User(
            username=f'user_{uuid.uuid4().hex[:6]}',
            email=f'{role.value}_{uuid.uuid4().hex[:6]}@test.com',
            hashed_password='$2b$12$EixZaYVK1fsbw1Zfbp36WQoeG6Lruj3vjPGGa31S2',
            role=role,
            is_active=True,
            cafe_id=cafe_id,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    return _create_user


@pytest.fixture
async def test_user(create_user: Callable[..., Awaitable[User]]) -> User:
    """Создает обычного пользователя."""
    return await create_user(role=Role.USER)


@pytest.fixture
async def test_admin(create_user: Callable[..., Awaitable[User]]) -> User:
    """Создает админа."""
    return await create_user(role=Role.ADMIN)


@pytest.fixture
async def user_headers(test_user: User) -> dict[str, str]:
    """Создает заголовки обычного пользователя."""
    token = create_access_token(data={'sub': str(test_user.id)})
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
async def admin_headers(test_admin: User) -> dict[str, str]:
    """Создает заголовки админа."""
    token = create_access_token(data={'sub': str(test_admin.id)})
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
async def manager_headers(
    session: AsyncSession,
    create_user: Callable[..., Awaitable[User]],
    test_cafe: Cafe,
) -> dict[str, str]:
    """Заголовки для менеджера, привязанного к тестовому кафе."""
    manager = await create_user(role=Role.MANAGER, cafe_id=test_cafe.id)
    await session.commit()
    token = create_access_token(data={'sub': str(manager.id)})
    return {'Authorization': f'Bearer {token}'}
