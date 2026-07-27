from datetime import date
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.sql.base import ExecutableOption

from src.bookings.models import Booking, TableSlot
from src.bookings.schemas import BookingCreate, BookingUpdate
from src.core.constants import BookingStatus as BStatus
from src.crud.crud import CRUDBase
from src.db.models_for_alembic import Cafe, Table


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

    async def get_bookings(
        self,
        db: AsyncSession,
        cafe_id: UUID | None = None,
        user_id: UUID | None = None,
        is_active: bool = True,
        booking_date: date | None = None,
    ) -> list[Booking]:
        """Универсальный метод получения списка бронирований.

        Args:
            db (AsyncSession): Асинхронная сессия базы данных.
            cafe_id (UUID | None): ID кафе для фильтрации.
            user_id (UUID | None): ID пользователя для фильтрации.
            is_active (bool): Фильтр по активности.
            booking_date (date | None): Опциональный фильтр по дате.

        Returns:
            list[Booking]: Список объектов бронирований.

        """
        query = (
            select(self.model)
            .options(*self._get_complex_options())
            .where(self.model.is_active == is_active)
        )
        if cafe_id:
            query = (
                query.join(self.model.tables_slots)
                .join(TableSlot.table)
                .where(Table.cafe_id == cafe_id)
            )
        if user_id:
            query = query.where(self.model.user_id == user_id)
        if booking_date:
            query = query.where(self.model.booking_date == booking_date)
        result = await db.execute(query)
        return list(result.unique().scalars().all())

    async def update_booking_object(
        self,
        db: AsyncSession,
        booking: Booking,
        update_data: BookingUpdate,
    ) -> Booking:
        """Обновляет поля бронирования из пришедшей схемы.

        Args:
            db (AsyncSession): Асинхронная сессия базы данных.
            booking (Booking): Существующий объект бронирования.
            update_data (BookingUpdate): Схема с данными для обновления.

        Returns:
            Booking: Обновленный объект бронирования.

        """
        obj_data = update_data.model_dump(exclude_unset=True)

        for key, value in obj_data.items():
            setattr(booking, key, value)

            if key == 'status' and value == BStatus.CANCELED:
                booking.is_active = False

        await db.commit()
        await db.refresh(booking)
        return booking

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
            status=BStatus.BOOKING,
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

    async def deactivate_booking(
        self,
        db: AsyncSession,
        booking: Booking,
    ) -> Booking:
        """Мягко удаляет бронирование.

        Переводит бронь в статус CANCELED, деактивирует её и
        автоматически освобождает все связанные слоты столов.

        Args:
            db (AsyncSession): Асинхронная сессия базы данных.
            booking (Booking): Объект бронирования для отмены.

        Returns:
            Booking: Деактивированный объект бронирования.

        """
        booking.is_active, booking.status = False, BStatus.CANCELED
        await db.execute(
            update(TableSlot)
            .where(TableSlot.booking_id == booking.id)
            .values(booking_id=None),
        )
        await db.commit()
        await db.refresh(booking)
        return booking


booking_crud = BookingCRUD(Booking)
