from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bookings.crud import booking_crud
from src.bookings.models import Booking, TableSlot
from src.bookings.notifications import (
    schedule_notifications_on_create,
    schedule_notifications_on_update,
)
from src.bookings.schemas import BookingCreate, BookingUpdate
from src.bookings.validators import (
    check_booking_collision,
    validate_booking_access,
    validate_booking_availability,
    validate_manager_access,
    validate_slot_not_in_past,
    validate_slots_availability,
)
from src.core.constants import Role
from src.core.logger import get_logger
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

        await validate_slot_not_in_past(
            booking_date=booking_data.booking_date,
            start_time=start_time,
        )

        await check_booking_collision(
            db=db,
            user_id=user_id,
            start_time=start_time,
            booking_date=booking_data.booking_date,
        )
        await validate_booking_availability(
            db=db,
            booking_date=booking_data.booking_date,
            items=booking_data.tables_slots,
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
        """Реализует логику мягкого удаления бронирования.

        Меняет флаг is_active на False и освобождает связанный слот.

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
        if not booking.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Бронирование уже отменено или неактивно',
            )
        deact_booking = await booking_crud.deactivate_booking(db, booking)
        logger.debug('Деактивировано бронирование %s', deact_booking.id)
        schedule_notifications_on_update(deact_booking)
        return deact_booking

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
        if not user.cafe_id and user.role != Role.ADMIN:
            logger.warning('Пользователь %s не прикреплен к кафе', user.id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Вы не закреплены ни за одним кафе',
            )

        users_cafe_id = cafe_id if user.role == Role.ADMIN else user.cafe_id

        bookings = await booking_crud.get_bookings(
            db=db,
            cafe_id=cafe_id or user.cafe_id,
            user_id=user_id,
            booking_date=booking_date,
            is_active=is_active,
        )
        logger.debug('Получены бронирования для кафе %s', users_cafe_id)
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

        if booking_data.tables_slots is not None:
            logger.debug(
                'Запрошено изменение столов для бронирования %s',
                booking_id,
            )
            await validate_slots_availability(
                db=db,
                booking_date=booking_data.booking_date or booking.booking_date,
                tables_slots=booking_data.tables_slots,
            )

            stmt = select(TableSlot).where(
                TableSlot.id.in_(booking_data.tables_slots),
            )
            result = await db.execute(stmt)
            slots_objects = list(result.scalars().all())

            if len(slots_objects) != len(booking_data.tables_slots):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Один или несколько столов не найдены',
                )

            booking_data.tables_slots = slots_objects

        updated_booking = await booking_crud.update(
            session=db,
            db_obj=booking,
            obj_in=booking_data,
        )
        logger.debug('Обновлено бронирование %s', updated_booking.id)
        schedule_notifications_on_update(updated_booking)
        return updated_booking


booking_service = BookingService()
