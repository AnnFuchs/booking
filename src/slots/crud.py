import uuid
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud import CRUDBase
from src.slots.models import Slot


class CRUDTimeSlot(CRUDBase[Slot]):
    """Класс, описывающий CRUD методы модели TimeSlot."""

    async def get_overlapping_slot(
        self,
        session: AsyncSession,
        cafe_id: uuid.UUID,
        start_time: Any,
        end_time: Any,
        exclude_slot_id: Optional[uuid.UUID] = None,
    ) -> Optional[Slot]:
        """Возвращает первый пересекающийся слот или None.

        Использует FOR UPDATE на пересекающихся строках напрямую,
        чтобы избежать лишней загрузки всех слотов кафе.
        """
        query = (
            select(Slot)
            .where(
                Slot.cafe_id == cafe_id,
                Slot.start_time < end_time,
                Slot.end_time > start_time,
            )
            .with_for_update(read=True)
        )
        if exclude_slot_id:
            query = query.where(Slot.id != exclude_slot_id)

        return (await session.execute(query)).scalar_one_or_none()


time_slot_crud = CRUDTimeSlot(Slot)
