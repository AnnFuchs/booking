from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import exists

from src.core.constants import Role
from src.crud.crud import CRUDBase
from src.db.models_for_alembic import Cafe, User


class CRUDCafe(CRUDBase[Cafe]):
    """CRUD класс для модели Cafe."""

    async def get_by_name_and_adress(
        self,
        name: str,
        address: str,
        session: AsyncSession,
    ) -> Cafe | None:
        """Получение кафе по названию и адресу."""
        result = await session.execute(
            select(self.model)
            .where(self.model.name == name, self.model.address == address),
        )
        return result.scalar_one_or_none()

    async def get_cafe_with_managers_preload(
        self,
        session: AsyncSession,
        cafe_id: UUID,
    ) -> Cafe:
        """Получение кафе с подгруженной таблицей менеджеров."""
        result = await session.execute(
            select(self.model)
            .where(self.model.id == cafe_id)
            .options(
                selectinload(
                    self.model.managers.and_(User.role == Role.MANAGER),
                ),
            ),
        )
        return result.scalars().first()

    async def exists(
        self,
        session: AsyncSession,
        cafe_id: UUID,
    ) -> bool:
        """Проверка существования кафе с заданным id."""
        result = await session.execute(
            select(exists().where(Cafe.id == cafe_id)),
        )
        return result.scalar()


cafe_crud = CRUDCafe(Cafe)
