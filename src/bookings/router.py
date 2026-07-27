from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_user_by_role
from src.bookings.dependencies import (
    validate_booking_request,
)
from src.bookings.models import Booking, TableSlot
from src.bookings.schemas import BookingCreate, BookingInfo, BookingUpdate
from src.bookings.service import booking_service
from src.core.constants import ALL_ROLE, Role
from src.db.session import get_async_session
from src.users.models import User

router = APIRouter(prefix='/booking', tags=['Бронирования'])


@router.get(
    '',
    response_model=list[BookingInfo],
    summary='Получение списка бронирований',
    description=(
        'Получение списка бронирований. '
        'Для администраторов и менеджеров - все бронирования '
        '(с возможностью выбора), для пользователей - только свои '
        '(параметры игнорируются, кроме ID кафе)'
    ),
)
async def get_bookings(
    show_active: bool = Query(
        True,
        description=(
            'Показывать все бронирования, '
            'только активные или только не активные. '
            'По умолчанию показывает только активные бронирования.'
        ),
    ),
    cafe_id: UUID | None = Query(
        None,
        description='ID кафе, в котором показывать бронирования. '
        'Если не задано - показывает все бронирования во всех кафе',
    ),
    user_id: UUID | None = Query(
        None,
        description='ID пользователя, бронирования которого показывать. '
        'Если не задано - показывает бронирования всех пользователей',
    ),
    current_user: User = Depends(get_user_by_role(ALL_ROLE)),
    db: AsyncSession = Depends(get_async_session),
) -> list[Booking]:
    """Получение списка бронирований.

    Для администраторов и менеджеров - все бронирования
    (с возможностью выбора), для пользователей - только свои
    (параметры игнорируются, кроме ID кафе).
    """
    if current_user.role == Role.USER:
        return await booking_service.get_bookings_by_user_id(
            db,
            user_id=current_user.id,
            is_active=show_active,
        )

    return await booking_service.get_manager_bookings(
        db,
        user=current_user,
        cafe_id=cafe_id,
        user_id=user_id,
        is_active=show_active,
    )


@router.post(
    '',
    response_model=BookingInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Создание нового бронирования',
)
async def create_booking(
    booking_data: BookingCreate,
    table_slots: list[TableSlot] = Depends(validate_booking_request),
    current_user: User = Depends(get_user_by_role(ALL_ROLE)),
    db: AsyncSession = Depends(get_async_session),
) -> Booking:
    """Создает новое бронирования.

    Только для авторизированных пользователей.
    """
    return await booking_service.create_booking(
        db=db,
        user_id=current_user.id,
        booking_data=booking_data,
        table_slots=table_slots,
    )


@router.get(
    '/{booking_id}',
    response_model=BookingInfo,
    summary='Получение информации о бронировании по его ID',
)
async def get_booking_with_details(
    booking_id: UUID,
    current_user: User = Depends(get_user_by_role(ALL_ROLE)),
    db: AsyncSession = Depends(get_async_session),
) -> Booking:
    """Получение информации о бронировании по его ID.

    Для администраторов и менеджеров - все бронирования, для пользователей -
    только свои.
    """
    return await booking_service.get_booking_with_details(
        db,
        booking_id,
        current_user,
    )


@router.patch(
    '/{booking_id}',
    response_model=BookingInfo,
    summary='Обновление информации о бронировании по его ID',
)
async def update_booking(
    booking_id: UUID,
    booking_data: BookingUpdate,
    current_user: User = Depends(get_user_by_role(ALL_ROLE)),
    db: AsyncSession = Depends(get_async_session),
) -> Booking:
    """Обновление информации об акции по ее ID.

    Только для администраторов и менеджеров.
    """
    return await booking_service.update_booking(
        db=db,
        booking_id=booking_id,
        booking_data=booking_data,
        user=current_user,
    )
