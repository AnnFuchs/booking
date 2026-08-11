from typing import Any, Optional
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud.crud import CRUDBase
from src.crud.utils import build_filter_conditions
from src.users.models import User


class UserCRUD(CRUDBase[User]):
    """CRUD для пользователей."""

    def __init__(self) -> None:
        """Инициализация."""
        super().__init__(User)

    async def get_by_login(
        self,
        session: AsyncSession,
        login: str,
    ) -> User | None:
        """Получение экземпляра пользователя по логину."""
        return await session.scalar(
            select(User).where(
                or_(User.email == login, User.phone == login),
                User.is_active,
            ),
        )

    async def get_by_any_attribute(
        self,
        session: AsyncSession,
        filters: dict[str, Any],
        exclude_id: UUID | None = None,
    ) -> Optional[User]:
        """Получение пользователя, соответствующего хотя бы одному фильтру."""
        conditions = build_filter_conditions(self.model, filters)
        if not conditions:
            return None

        query = select(self.model).where(or_(*conditions))
        if exclude_id:
            query = query.where(self.model.id != exclude_id)

        return (await session.execute(query)).scalars().first()

    async def save(self, session: AsyncSession, user: User) -> User:
        """Сохранение существующего или нового экземпляра пользователя."""
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


user_crud = UserCRUD()
