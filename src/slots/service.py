from datetime import time
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.bookings.service import table_slot_service
from src.cafes.crud import cafe_crud
from src.core.constants import (
    STAFF_ROLE,
)
from src.core.logger import get_logger
from src.db.utils import get_or_404
from src.slots.crud import time_slot_crud
from src.slots.errors import SlotOverlapError
from src.slots.models import Slot
from src.slots.schemas import TimeSlotCreate, TimeSlotUpdate
from src.slots.utils import validate_slot_time
from src.slots.validators import check_user_cafe_access
from src.users.models import User

logger = get_logger(__name__)


class SlotService:
    """Сервисный слой для работы с временными слотами."""

    async def _check_slot_overlap(
        self,
        session: AsyncSession,
        *,
        cafe_id: UUID,
        start_time: time,
        end_time: time,
        exclude_slot_id: Optional[UUID] = None,
    ) -> None:
        """Проверяет пересечение нового временного слота с существующими в БД.

        Args:
            session: Сессия БД.
            cafe_id: ID кафе, для которого создается слот.
            start_time: Время начала нового слота.
            end_time: Время окончания нового слота.
            exclude_slot_id: ID слота, который нужно исключить (для обновления)

        Raises:
            HTTPException: (400) Если слот пересекается с существующим.

        """
        existing_slot = await time_slot_crud.get_overlapping_slot(
            session,
            cafe_id=cafe_id,
            start_time=start_time,
            end_time=end_time,
            exclude_slot_id=exclude_slot_id,
        )
        if existing_slot:
            logger.warning(
                'Переданный слот пересекается с существующим слотом %s',
                existing_slot,
            )
            raise SlotOverlapError(
                'Переданный слот пересекается '
                f'с существующим слотом {existing_slot}',
            )

    async def create_time_slot(
        self,
        session: AsyncSession,
        time_slot: TimeSlotCreate,
        cafe_id: UUID,
        current_user: User,
    ) -> Slot:
        """Валидирует права доступа и создаёт временной слот."""
        await check_user_cafe_access(session, current_user, cafe_id)
        await self._check_slot_overlap(
            session,
            cafe_id=cafe_id,
            start_time=time_slot.start_time,
            end_time=time_slot.end_time,
        )
        try:
            slot = await time_slot_crud.create(
                session,
                obj_in=time_slot,
                cafe_id=cafe_id,
                commit=False,
            )
            await table_slot_service.create(session, slot, cafe_id)

            await session.commit()
            await session.refresh(slot)

            logger.debug(
                'Пользователем %s создан слот %s',
                current_user.id,
                slot.id,
            )
            return slot

        except Exception:
            await session.rollback()
            raise

    async def update_time_slot(
        self,
        session: AsyncSession,
        time_slot_id: UUID,
        obj_in: TimeSlotUpdate,
        cafe_id: UUID,
        current_user: User,
    ) -> Slot:
        """Валидирует права доступа и обновляет временной слот."""
        await check_user_cafe_access(session, current_user, cafe_id)

        time_slot = await get_or_404(
            session,
            time_slot_crud,
            time_slot_id,
            detail='Слот не найден.',
            filters={'cafe_id': cafe_id},
            log_msg=f'Слот с id {time_slot_id} не найден.',
        )
        validate_slot_time(
            start_time=(
                obj_in.start_time
                if obj_in.start_time is not None
                else time_slot.start_time
            ),
            end_time=(
                obj_in.end_time
                if obj_in.end_time is not None
                else time_slot.end_time
            ),
        )
        await self._check_slot_overlap(
            session,
            cafe_id=cafe_id,
            start_time=(
                obj_in.start_time
                if obj_in.start_time is not None
                else time_slot.start_time
            ),
            end_time=(
                obj_in.end_time
                if obj_in.end_time is not None
                else time_slot.end_time
            ),
            exclude_slot_id=time_slot.id,
        )
        try:
            slot = await time_slot_crud.update(
                session,
                time_slot,
                obj_in,
                commit=False,
            )

            if obj_in.is_active and not time_slot.is_active:
                await table_slot_service.create(session, slot, cafe_id)
            if obj_in.is_active is False and time_slot.is_active:
                await table_slot_service.deactivate_for_slot(
                    session,
                    slot.id,
                    commit=False,
                )

            await session.commit()
            await session.refresh(slot)

            logger.debug(
                'Пользователь %s обновил слот %s',
                current_user.id,
                slot.id,
            )
            return slot

        except Exception:
            await session.rollback()
            raise

    async def get_time_slots(
        self,
        session: AsyncSession,
        cafe_id: UUID,
        current_user: User,
        show_active: bool,
    ) -> list[Slot]:
        """Возвращает список слотов с учётом роли пользователя.

        Raises:
            HTTPException: (404) Если кафе не найдено.

        """
        if current_user.role not in STAFF_ROLE:
            show_active = True
            logger.debug(
                'Пользователь %s (роль: %s) — принудительно show_active=True',
                current_user.id,
                current_user.role,
            )

        cafe = await get_or_404(
            session,
            cafe_crud,
            cafe_id,
            detail='Кафе не найдено.',
            log_msg=f'Кафе с id {cafe_id} не найдено.',
        )
        filters: dict = {'cafe_id': cafe.id}
        if show_active is not None:
            filters['is_active'] = show_active
        slots = await time_slot_crud.get_multi(session, filters=filters)
        logger.debug(
            'Пользователь %s запросил список слотов кафе %s'
            '(show_active=%s, найдено=%s)',
            current_user.id,
            cafe_id,
            show_active,
            len(slots),
        )
        return list(slots)

    async def get_time_slot_by_id(
        self,
        session: AsyncSession,
        cafe_id: UUID,
        slot_id: UUID,
        active_only: bool = False,
    ) -> Slot:
        """Возвращает слот по ID с фильтром по кафе.

        Raises:
            HTTPException: (404) Если слот или кафе не найдены.

        """
        cafe = await get_or_404(
            session,
            cafe_crud,
            cafe_id,
            detail='Кафе не найдено.',
            log_msg=f'Кафе с id {cafe_id} не найдено.',
        )
        filters: dict = {'cafe_id': cafe.id}
        if active_only:
            filters['is_active'] = True
        slot = await time_slot_crud.get(
            session,
            obj_id=slot_id,
            filters=filters,
        )
        slot = await get_or_404(
            session,
            time_slot_crud,
            slot_id,
            detail='Слот не найден.',
            filters=filters,
            log_msg=(
                f'Слот с id {slot_id} в кафе {cafe_id} не найден'
                '(active_only={active_only})',
            ),
        )
        logger.debug(
            'Получен слот %s в кафе %s',
            slot_id,
            cafe_id,
        )
        return slot


slot_service = SlotService()
