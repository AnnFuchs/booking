from datetime import date, datetime, time
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.bookings.crud import booking_crud
from src.bookings.models import Booking, TableSlot
from src.bookings.schemas import BookingTableSlot
from src.bookings.utils import validate_date_not_in_past
from src.core.constants import MAX_BOOKINGS_PER_USER, Role
from src.core.logger import get_logger
from src.users.models import User

logger = get_logger(__name__)


def _check_cafe_permission(
    user: User,
    booking: Booking,
    error_msg: str,
) -> None:
    """Внутренняя логика проверки принадлежности к кафе.

    Args:
        user (User): Объект текущего пользователя.
        booking (Booking): Объект бронирования для проверки.
        error_msg (str): Текст сообщения об ошибке для пользователя.

    Raises:
        HTTPException: Попытка получить доступ к чужому кафе.

    """
    if user.role == Role.MANAGER:
        if user.cafe_id is None:
            logger.warning(
                f'Пользователь не прикреплен к кафе. Детали: {error_msg}',
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Доступ запрещен',
            )
        if (
            not booking.tables_slots
            or booking.tables_slots[0].table.cafe_id != user.cafe_id
        ):
            logger.warning(
                f'Попытка доступа к чужому кафе. Детали: {error_msg}',
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Доступ запрещен',
            )


async def validate_slot_not_in_past(
    booking_date: date,
    start_time: time,
) -> None:
    """Проверяет, что время начала бронирования не находится в прошлом.

    Args:
        start_time: Время начала слота для проверки.
        booking_date (date | None): Опциональный фильтр по дате.

    Raises:
        HTTPException: Если время меньше текущего.

    """
    try:
        validate_date_not_in_past(booking_date)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    booking_datetime = datetime.combine(booking_date, start_time)
    if booking_datetime < datetime.now():
        logger.warning(
            'Переданное время бронирования уже прошло: %s %s.',
            booking_date,
            start_time,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Нельзя забронировать время в прошлом',
        )


async def check_user_booking_limit(
    db: AsyncSession,
    user_id: UUID,
    limit: int = MAX_BOOKINGS_PER_USER,
) -> None:
    """Проверяет лимит активных бронирований пользователя.

    Args:
        db (AsyncSession): Асинхронная сессия базы данных.
        user_id (UUID): Идентификатор пользователя.
        limit (int): Максимально допустимое количество бронирований.

    Raises:
        HTTPException : 400 Если лимит бронирований исчерпан.

    """
    count = await booking_crud.get_and_count_bookings_for_user(
        db,
        user_id,
    )
    if count >= limit:
        logger.warning(
            'Превышен лимит активных бронирований (макс: %s)',
            limit,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Превышен лимит активных бронирований (макс: {limit})',
        )


async def check_booking_collision(
    db: AsyncSession,
    user_id: UUID,
    start_time: time,
    booking_date: date,
) -> None:
    """Проверяет наличие у пользователя других броней на то же время.

    Args:
        db: Сессия базы данных.
        user_id: ID пользователя.
        start_time: Время начала слота.
        booking_date: Дата брони.

    Raises:
        HTTPException: Если найдено пересечение по времени.

    """
    collision = await booking_crud.get_bookings(
        db=db,
        user_id=user_id,
        booking_date=booking_date,
        start_time=start_time,
    )
    if collision:
        logger.warning('Попытка брони на то же время в другом заведении.')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='У вас уже есть бронь на это время в другом заведении',
        )


async def validate_manager_access(user: User, booking: Booking) -> None:
    """Проверяет права менеджера на управление конкретным бронированием.

    Args:
        user: Объект текущего пользователя.
        booking: Объект бронирования.

    """
    if user.role == Role.ADMIN:
        return
    _check_cafe_permission(
        user,
        booking,
        'У вас нет прав на управление бронированиями в этом кафе',
    )


def validate_manager_cafe_permission(user: User, booking: Booking) -> None:
    """Проверяет, что менеджер работает в том же кафе, где создана бронь.

    Args:
        user: Объект текущего пользователя.
        booking: Объект бронирования.

    """
    if user.role == Role.ADMIN:
        return
    _check_cafe_permission(
        user,
        booking,
        'Менеджер может управлять бронями только своего кафе',
    )


async def validate_booking_access(user: User, booking: Booking) -> None:
    """Проверяет права доступа к бронированию для всех ролей.

    Args:
        user: Объект текущего пользователя.
        booking: Объект бронирования.

    Raises:
        HTTPException: 403 для менеджеров при чужом кафе,
                       404 для юзеров при чужой брони.

    """
    if user.role == Role.ADMIN:
        return

    if user.role == Role.MANAGER:
        validate_manager_cafe_permission(user, booking)
        return

    if booking.user_id != user.id:
        logger.warning('Id пользователя не совпадает для booking и для user.')
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Бронирование не найдено',
        )


async def validate_booking_for_cancellation(
    user: User,
    booking: Booking | None,
) -> None:
    """Валидация перед отменой бронирования.

    Args:
        user (User): Объект текущего пользователя.
        booking (Booking | None): Объект бронирования, полученный из БД.

    Raises:
        HTTPException: 404 Бронирование не найдено.
        HTTPException: 400 Бронирование уже отменено.
        HTTPException: 403 Недостаточно прав.

    """
    if not booking:
        logger.warning('Бронирование не найдено.')
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Бронирование не найдено',
        )

    await validate_booking_access(user, booking)

    if not booking.is_active:
        logger.warning('Бронирование не активно.')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Бронирование уже отменено',
        )


async def validate_slots_availability(
    db: AsyncSession,
    booking_date: date,
    tables_slots: list[BookingTableSlot],
) -> list[TableSlot]:
    """Проверяет доступность списка столов на конкретную дату.

    Выполняет валидацию:
    1. Проверка даты (нельзя бронировать задним числом).
    2. Проверка существования каждой пары стол-слот.
    3. Проверка статуса и отсутствия существующих броней.

    Args:
        db (AsyncSession): Асинхронная сессия базы данных.
        booking_date (date): Дата планируемого визита.
        tables_slots (list[BookingTableSlot]): Список пар стол-слот.

    Returns:
        list[TableSlot]: Список найденных и проверенных объектов TableSlot.

    Raises:
        HTTPException : 400 если стол недоступен/занят.

    """
    pairs = [(item.table_id, item.slot_id) for item in tables_slots]

    found_slots = await booking_crud.get_available_tableslots(
        db,
        pairs,
        booking_date,
    )

    found_by_pair = {(ts.table_id, ts.slot_id): ts for ts in found_slots}

    for item in tables_slots:
        pair = (item.table_id, item.slot_id)
        slot = found_by_pair.get(pair)

        if slot is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Слот для стола не найден.',
            )
        if slot.booking_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Стол на выбранное время уже забронирован.',
            )

    return found_slots
