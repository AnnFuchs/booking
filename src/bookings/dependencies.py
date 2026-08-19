from uuid import UUID

from fastapi import Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_user_by_role
from src.bookings.crud import booking_crud
from src.bookings.models import Booking, TableSlot
from src.bookings.schemas import BookingCreate
from src.bookings.validators import (
    check_user_booking_limit,
    validate_booking_for_cancellation,
    validate_slots_availability,
)
from src.core.constants import ALL_ROLE
from src.db.session import get_async_session
from src.users.models import User


async def validate_booking_request(
    booking_data: BookingCreate = Body(...),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_user_by_role(ALL_ROLE)),
) -> list[TableSlot]:
    """Зависимость для комплексной валидации бронирования перед созданием."""
    await check_user_booking_limit(db, current_user.id)

    return await validate_slots_availability(
        db=db,
        booking_date=booking_data.booking_date,
        tables_slots=booking_data.tables_slots,
        cafe_id=booking_data.cafe_id,
        for_update=True,
    )


async def get_valid_booking_for_cancel(
    booking_id: UUID,
    current_user: User = Depends(get_user_by_role(ALL_ROLE)),
    db: AsyncSession = Depends(get_async_session),
) -> Booking:
    """Зависимость для проверки прав и статуса бронирования перед отменой."""
    booking = await booking_crud.get_booking_with_details(db, booking_id)

    await validate_booking_for_cancellation(current_user, booking)

    return booking
