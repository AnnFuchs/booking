from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.bookings.crud import booking_crud, table_slot_crud
from src.bookings.models import Booking, TableSlot
from src.bookings.notifications import (
    schedule_notifications_on_create,
    schedule_notifications_on_slot_status_change,
    schedule_notifications_on_update,
)
from src.bookings.schemas import BookingCreate, BookingTableSlot, BookingUpdate
from src.bookings.validators import (
    check_booking_collision,
    validate_booking_access,
    validate_manager_access,
    validate_slot_not_in_past,
    validate_slots_availability,
)
from src.core.constants import TABLE_SLOT_ADVANCE_DAYS, BookingStatus, Role
from src.core.logger import get_logger
from src.slots.models import Slot
from src.tables.crud import table_crud
from src.users.models import User

logger = get_logger(__name__)


class BookingService:
    """Класс сервиса для управления бизнес-логикой бронирований.

    Связывает API (роутеры) с CRUD-слоем и применяет правила валидации.
    """

    async def create_booking(
        self,
        db: AsyncSession,
        user_id: UUID,
        booking_data: BookingCreate,
        table_slots: list[TableSlot],
    ) -> Booking:
        """Обрабатывает логику создания бронирования.

        Включает проверку доступности слота и лимитов пользователя.

        Args:
            db: Асинхронная сессия базы данных.
            user_id (UUID): Идентификатор пользователя
            booking_data: Данные из тела запроса.
            table_slots: Список объектов TableSlot у бронирования.

        Returns:
            Объект созданного бронирования.

        """
        logger.debug(
            'Пользователь %s создаёт бронирование для кафе %s.',
            user_id,
            booking_data.cafe_id,
        )
        start_time = table_slots[0].slot.start_time
        end_time = table_slots[0].slot.end_time

        await validate_slot_not_in_past(
            booking_date=booking_data.booking_date,
            start_time=start_time,
        )

        await check_booking_collision(
            db=db,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            booking_date=booking_data.booking_date,
        )

        new_booking = await booking_crud.create_booking(
            db,
            user_id=user_id,
            booking_data=booking_data,
            table_slots=table_slots,
        )

        logger.debug('Создано бронирование %s', new_booking.id)
        schedule_notifications_on_create(new_booking)
        return new_booking

    async def cancel_booking(
        self,
        db: AsyncSession,
        booking: Booking,
        user: User,
    ) -> Booking:
        """Реализует логику отмены бронирования.

        Меняет статус на CANELED и освобождает связанный слот.

        Args:
            db: Асинхронная сессия базы данных.
            booking: Объект бронирования для отмены.
            user: Объект текущего пользователя.

        Returns:
            Объект обновленного бронирования.

        Raises:
            HTTPException: Если бронирование не найдено или уже неактивно.

        """
        await validate_manager_access(user=user, booking=booking)
        if not booking.is_active or booking.status is BookingStatus.CANCELED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Бронирование уже отменено или неактивно',
            )
        canceled_booking = await booking_crud.cancel_booking(db, booking)
        logger.debug('Отменено бронирование %s', canceled_booking.id)
        schedule_notifications_on_update(canceled_booking)
        return canceled_booking

    async def get_booking_with_details(
        self,
        db: AsyncSession,
        booking_id: UUID,
        user: User,
    ) -> Booking:
        """Возвращает бронирование по ID.

        Args:
            db: Сессия базы данных.
            booking_id: ID бронирования.
            user: Объект текущего пользователя.

        Returns:
            Объект бронирования.

        Raises:
            HTTPException: Если бронирование не найдено.

        """
        booking = await booking_crud.get_booking_with_details(db, booking_id)
        if not booking:
            logger.warning('Бронирование с id %s не найдено', booking_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Бронирование не найдено',
            )

        await validate_booking_access(user, booking)
        logger.debug('Найдено бронирование %s', booking_id)
        return booking

    async def get_bookings_by_user_id(
        self,
        db: AsyncSession,
        user_id: UUID,
        is_active: bool = True,
    ) -> list[Booking]:
        """Получает список бронирований пользователя.

        Args:
            db (AsyncSession): Асинхронная сессия базы данных.
            user_id (UUID): Идентификатор пользователя.
            is_active (bool): Флаг бронирований.

        Returns:
            list[Booking]: Список объектов бронирований пользователя.

        """
        bookings = await booking_crud.get_bookings_by_user_id(
            db=db,
            user_id=user_id,
            is_active=is_active,
        )
        logger.debug('Получены бронирования пользователя %s', user_id)
        return bookings

    async def get_manager_bookings(
        self,
        db: AsyncSession,
        user: User,
        cafe_id: UUID | None = None,
        user_id: UUID | None = None,
        is_active: bool = True,
        booking_date: date | None = None,
    ) -> list[Booking]:
        """Получает бронирования кафе для менеджера.

        Args:
            db (AsyncSession): Асинхронная сессия базы данных.
            user (User): Объект текущего пользователя (менеджера или админа).
            cafe_id (UUID): Идентификатор кафе.
            user_id (UUID): Идентификатор пользователя.
            is_active (bool): Флаг бронирований.
            booking_date (date | None): Фильтр по дате бронирования.

        Returns:
            list[Booking]: Список бронирований.

        Raises:
            HTTPException: Если менеджер не привязан к кафе и не админ.

        """
        if user.role != Role.ADMIN:
            if not user.cafe_id:
                logger.warning('Пользователь %s не прикреплен к кафе', user.id)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail='Вы не закреплены ни за одним кафе',
                )
            cafe_id = user.cafe_id

        bookings = await booking_crud.get_bookings(
            db=db,
            cafe_id=cafe_id,
            user_id=user_id,
            booking_date=booking_date,
            is_active=is_active,
        )
        logger.debug('Получены бронирования для кафе %s', cafe_id)
        return bookings

    async def update_booking(
        self,
        db: AsyncSession,
        booking_id: UUID,
        booking_data: BookingUpdate,
        user: User,
    ) -> Booking:
        """Обновляет бронирования.

        Обрабатывает изменение бронирования, логику отмены
        и перебронирование списка столов с проверкой их доступности.

        Args:
            db (AsyncSession): Асинхронная сессия базы данных.
            booking_id (UUID): Идентификатор обновляемого бронирования.
            booking_data (BookingUpdate): Схема с новыми данными.
            user (User): Объект текущего пользователя для проверки прав.

        Returns:
            Booking: Обновленный объект бронирования с подгруженными данными.

        """
        logger.debug(
            'Пользователь %s обновляет бронирование %s.',
            user.id,
            booking_id,
        )

        booking = await self.get_booking_with_details(db, booking_id, user)
        await validate_manager_access(user=user, booking=booking)

        if booking_data.is_active is False:
            logger.debug('Запрошена деактивация бронирования %s', booking.id)
            return await booking_crud.deactivate_booking(db, booking)

        if booking_data.status is BookingStatus.CANCELED:
            logger.debug('Запрошена отмена бронирования %s', booking.id)
            return await self.cancel_booking(db, booking, user)

        if booking_data.tables_slots is not None:
            logger.debug(
                'Запрошено изменение столов для бронирования %s',
                booking_id,
            )
            slots_objects = await validate_slots_availability(
                db=db,
                booking_date=booking_data.booking_date or booking.booking_date,
                tables_slots=booking_data.tables_slots,
                cafe_id=booking.cafe_id,
                for_update=True,
                current_booking_id=booking.id,
            )

            booking.tables_slots = slots_objects
            # Так как slots_object это ORM-объекты, обновляем ORM-связь.
            booking_data.tables_slots = None
        elif (
            booking_data.booking_date is not None
            and booking_data.booking_date != booking.booking_date
        ):
            logger.debug(
                'Запрошено изменение даты без изменения столов для '
                'бронирования %s, проверяем доступность текущих столов '
                'на новую дату %s',
                booking_id,
                booking_data.booking_date,
            )
            same_tables_slots = [
                BookingTableSlot(
                    table_id=table_slot.table_id,
                    slot_id=table_slot.slot_id,
                )
                for table_slot in booking.tables_slots
            ]
            slots_objects = await validate_slots_availability(
                db=db,
                booking_date=booking_data.booking_date,
                tables_slots=same_tables_slots,
                cafe_id=booking.cafe_id,
                for_update=True,
                current_booking_id=booking.id,
            )

            booking.tables_slots = slots_objects

        updated_booking = await booking_crud.update(
            session=db,
            db_obj=booking,
            obj_in=booking_data,
        )
        logger.debug('Обновлено бронирование %s', updated_booking.id)
        schedule_notifications_on_update(updated_booking)
        return updated_booking


class TableSlotService:
    """Класс сервиса для управления бизнес-логикой связи столов и слотов."""

    async def create(
        self,
        session: AsyncSession,
        slot: Slot,
        cafe_id: UUID,
    ) -> None:
        """Создаёт TableSlot записи для всех активных столов кафе.

        Идемпотентно: реактивирует уже существующие (ранее деактивированные)
        записи и создаёт только недостающие, чтобы не нарушать
        UniqueConstraint('table_id', 'slot_id', 'booking_date').
        """
        tables = await table_crud.get_multi(
            session=session,
            filters={'cafe_id': cafe_id, 'is_active': True},
        )

        now_utc = datetime.now(timezone.utc)
        today = now_utc.date()
        first_date = today
        slot_start_today = datetime.combine(
            today,
            slot.start_time,
            timezone.utc,
        )
        if slot_start_today <= now_utc:
            first_date = today + timedelta(days=1)

        dates = [
            first_date + timedelta(days=delta)
            for delta in range(
                (
                    today
                    + timedelta(days=TABLE_SLOT_ADVANCE_DAYS)
                    - first_date
                ).days + 1,
            )
        ]

        expected_pairs = [
            (table.id, d) for table in tables for d in dates
        ]
        if not expected_pairs:
            return

        existing = await table_slot_crud.get_multi(
            session=session,
            filters={
                'slot_id': slot.id,
                'table_id__in': [t.id for t in tables],
                'booking_date__in': dates,
            },
        )
        existing_by_pair = {
            (ts.table_id, ts.booking_date): ts
            for ts in existing
            if ts.booking_date in dates
        }

        to_reactivate = [
            ts for ts in existing_by_pair.values() if not ts.is_active
        ]
        for ts in to_reactivate:
            ts.is_active = True

        new_table_slots = [
            TableSlot(table_id=table_id, slot_id=slot.id, booking_date=d)
            for table_id, d in expected_pairs
            if (table_id, d) not in existing_by_pair
        ]

        if new_table_slots:
            await table_slot_crud.bulk_create(session, new_table_slots)
        if new_table_slots or to_reactivate:
            logger.debug(
                'Создано %d и реактивировано %d TableSlot для слота %s',
                len(new_table_slots),
                len(to_reactivate),
                slot.id,
            )

    async def deactivate_for_slot(
        self,
        session: AsyncSession,
        slot_id: UUID,
        commit: bool = True,
    ) -> None:
        """Деактивирует небронированные TableSlot при отключении слота.

        По уже забронированным TableSlot (booking_id заполнен) статус
        НЕ меняется — вместо этого рассылается уведомление о том,
        что слот, на который забронирован стол, был отключен.

        Чтение "уже забронированных" и последующая деактивация свободных
        строк выполняются в рамках одной блокировки (FOR UPDATE), чтобы
        исключить гонку с параллельным созданием бронирования.
        """
        booked_table_slots = await table_slot_crud.get_booked_by_filters(
            session,
            slot_id=slot_id,
            from_date=datetime.now(timezone.utc).date(),
            for_update=True,
        )

        await table_slot_crud.deactivate_by_filters(
            session,
            slot_id=slot_id,
            from_date=datetime.now(timezone.utc).date(),
            commit=commit,
        )

        if booked_table_slots:
            schedule_notifications_on_slot_status_change(
                booked_table_slots,
                reason='Временной слот, на который вы забронировали стол, '
                       'был отключен администрацией кафе',
            )
            logger.debug(
                'Разослано %d уведомлений об отключении слота %s '
                'по существующим бронированиям',
                len(booked_table_slots),
                slot_id,
            )

    async def deactivate_for_table(
        self,
        session: AsyncSession,
        table_id: UUID,
        commit: bool = True,
    ) -> None:
        """Деактивирует небронированные TableSlot при отключении стола.

        По уже забронированным TableSlot (booking_id заполнен) статус
        НЕ меняется — вместо этого рассылается уведомление о том,
        что стол, на который сделана бронь, был отключен.

        Чтение "уже забронированных" и последующая деактивация свободных
        строк выполняются в рамках одной блокировки (FOR UPDATE), чтобы
        исключить гонку с параллельным созданием бронирования.
        """
        booked_table_slots = await table_slot_crud.get_booked_by_filters(
            session,
            table_id=table_id,
            from_date=datetime.now(timezone.utc).date(),
            for_update=True,
        )

        await table_slot_crud.deactivate_by_filters(
            session,
            table_id=table_id,
            from_date=datetime.now(timezone.utc).date(),
            commit=commit,
        )

        if booked_table_slots:
            schedule_notifications_on_slot_status_change(
                booked_table_slots,
                reason='Стол, который вы забронировали, '
                       'был отключен администрацией кафе',
            )
            logger.debug(
                'Разослано %d уведомлений об отключении стола %s '
                'по существующим бронированиям',
                len(booked_table_slots),
                table_id,
            )


booking_service = BookingService()
table_slot_service = TableSlotService()
