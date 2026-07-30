from datetime import date, time
from uuid import UUID

from sqlalchemy import func, select, tuple_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.sql.base import ExecutableOption

from src.bookings.models import Booking, TableSlot
from src.bookings.schemas import BookingCreate
from src.core.constants import BookingStatus
from src.crud.crud import CRUDBase
from src.db.models_for_alembic import Cafe, Slot, Table


class BookingCRUD(CRUDBase[Booking]):
    """CRUD класс для модели Booking с обходом системных ошибок."""

    def _get_complex_options(self) -> list[ExecutableOption]:
        """Возвращает список опций связанных сущностей бронирования."""
        return [
            selectinload(Booking.user),
            joinedload(Booking.cafe).selectinload(Cafe.managers),
            selectinload(Booking.tables_slots).options(
                joinedload(TableSlot.table).joinedload(Table.cafe),
                joinedload(TableSlot.slot),
            ),
        ]

    async def get_booking_with_details(
        self,
        db: AsyncSession,
        booking_id: UUID,
    ) -> Booking | None:
        """Получает бронирование по его уникальному идентификатору.

        Args:
            db (AsyncSession): Асинхронная сессия базы данных.
            booking_id (UUID): Идентификатор бронирования.

        Returns:
            Объект Booking со слотом и столом или None, если запись не найдена.

        """
        return await self.get(
            session=db,
            obj_id=booking_id,
            options=list(self._get_complex_options()),
        )

    async def get_bookings_by_user_id(
        self,
        db: AsyncSession,
        user_id: UUID,
        cafe_id: UUID | None = None,
        is_active: bool | None = None,
        booking_date: date = None,
    ) -> list[Booking]:
        """Возвращает список всех бронирований конкретного пользователя.

        Args:
            db (AsyncSession): Асинхронная сессия базы данных.
            user_id (UUID): Идентификатор пользователя.
            cafe_id (UUID | None): ID кафе для фильтрации.
            is_active: Статус активности (True для живых, False для удаленных).
            booking_date (date | None): Опциональный фильтр по дате.

        Returns:
            list[Booking]: Список объектов бронирований (может быть пустым).

        """
        filters = {}

        if user_id:
            filters['user_id'] = user_id

        if cafe_id:
            filters['cafe_id'] = cafe_id

        if is_active is not None:
            filters['is_active'] = is_active

        if booking_date:
            filters['booking_date'] = booking_date

        return await self.get_multi(session=db, filters=filters)

    async def get_and_count_bookings_for_user(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> int:
        """Возвращает число активных бронирований пользователя.

        Args:
            db (AsyncSession): Асинхронная сессия базы данных.
            user_id (UUID): Идентификатор пользователя.

        Returns:
            int: число активных бронирований пользователя с user_id.

        """
        query = (
            select(func.count())
            .select_from(Booking)
            .where(
                Booking.user_id == user_id,
                Booking.is_active,
                Booking.status == BookingStatus.BOOKING,
            ),
        )
        return (await db.execute(query)).scalar() or 0

    async def get_bookings(
        self,
        db: AsyncSession,
        cafe_id: UUID | None = None,
        user_id: UUID | None = None,
        is_active: bool = True,
        booking_date: date | None = None,
        start_time: time | None = None,
    ) -> list[Booking]:
        """Универсальный метод получения списка бронирований.

        Args:
            db (AsyncSession): Асинхронная сессия базы данных.
            cafe_id (UUID | None): ID кафе для фильтрации.
            user_id (UUID | None): ID пользователя для фильтрации.
            is_active (bool): Фильтр по активности.
            booking_date (date | None): Опциональный фильтр по дате.
            start_time (time | None): Опциональный фильтр по времени
                начала слота.

        Returns:
            list[Booking]: Список объектов бронирований.

        """
        query = (
            select(self.model)
            .options(*self._get_complex_options())
            .where(self.model.is_active == is_active)
        )
        if cafe_id or start_time:
            query = query.join(self.model.tables_slots)
            if cafe_id:
                query = query.join(
                    TableSlot.table,
                    ).where(
                        Table.cafe_id == cafe_id,
                        )
            if start_time:
                query = query.join(
                    TableSlot.slot,
                    ).where(
                        Slot.start_time == start_time,
                        )
        if user_id:
            query = query.where(self.model.user_id == user_id)
        if booking_date:
            query = query.where(self.model.booking_date == booking_date)
        result = await db.execute(query)
        return list(result.unique().scalars().all())

    async def get_available_tableslots(
        self,
        db: AsyncSession,
        expected_pairs: list[tuple[UUID, UUID]],
        booking_date: date,
    ) -> list[TableSlot]:
        """Получение всех объектов Tableslots для даты.

        Args:
            db (AsyncSession): Асинхронная сессия базы данных.
            expected_pairs (list[tuple[UUID, UUID]]): список кортежей
                из пар стол-слот.
            booking_date (date): Дата планируемого бронирования.

        Returns:
            Cписок найденных объектов TableSlot.

        """
        query = (
            select(TableSlot)
            .options(
                joinedload(TableSlot.slot),
                joinedload(TableSlot.table),
            )
            .where(
                tuple_(TableSlot.table_id, TableSlot.slot_id)
                .in_(expected_pairs),
                TableSlot.booking_date == booking_date,
                TableSlot.is_active,
                TableSlot.booking_id.is_(None),
            )
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def create_booking(
        self,
        db: AsyncSession,
        user_id: UUID,
        booking_data: BookingCreate,
        table_slots: list[TableSlot],
    ) -> Booking:
        """Создает новое бронирование и помечает слот как занятый.

        Args:
            db (AsyncSession): Асинхронная сессия базы данных.
            user_id (UUID): Идентификатор пользователя.
            booking_data: Схема с данными для создания (slot_id, comment).
            table_slots (list): Список слотов стола.

        Returns:
            Booking: Объект созданного бронирования с заполненными полями.

        """
        new_booking = Booking(
            user_id=user_id,
            cafe_id=booking_data.cafe_id,
            guest_number=booking_data.guest_number,
            note=booking_data.note,
            booking_date=booking_data.booking_date,
            status=BookingStatus.BOOKING,
        )
        db.add(new_booking)
        await db.flush()

        await db.execute(
            update(TableSlot)
            .where(TableSlot.id.in_([item.id for item in table_slots]))
            .values(booking_id=new_booking.id),
        )
        await db.commit()
        return await self.get_booking_with_details(db, new_booking.id)

    async def cancel_booking(
        self,
        db: AsyncSession,
        booking: Booking,
    ) -> Booking:
        """Отменяет бронирование.

        Меняет статус на CANCELED и автоматически освобождает
        все связанные слоты столов.

        Args:
            db (AsyncSession): Асинхронная сессия базы данных.
            booking (Booking): Объект бронирования для отмены.

        Returns:
            booking (Booking): Деактивированный объект бронирования.

        """
        booking.status = BookingStatus.CANCELED
        await db.execute(
            update(TableSlot)
            .where(TableSlot.booking_id == booking.id)
            .values(booking_id=None),
        )
        await db.commit()
        await db.refresh(booking)
        return booking

    async def deactivate_booking(
        self,
        db: AsyncSession,
        booking: Booking,
    ) -> Booking:
        """Мягко удаляет бронирование.

        Деактивирует бронь и автоматически освобождает
        все связанные слоты столов.

        Args:
            db (AsyncSession): Асинхронная сессия базы данных.
            booking (Booking): Объект бронирования для отмены.

        Returns:
            booking (Booking): Деактивированный объект бронирования.

        """
        booking.is_active = False
        await db.execute(
            update(TableSlot)
            .where(TableSlot.booking_id == booking.id)
            .values(booking_id=None),
        )
        await db.commit()
        await db.refresh(booking)
        return booking


booking_crud = BookingCRUD(Booking)
