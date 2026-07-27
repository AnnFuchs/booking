import uuid  # noqa: I001
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_user_by_role
from src.core.constants import ALL_ROLE, STAFF_ROLE
from src.core.logger import get_logger
from src.db.session import get_async_session
from src.slots.models import Slot
from src.slots.router_responses import (
    SLOT_CREATE_RESPONSES,
    SLOTS_LIST_RESPONSES,
    SLOT_GET_BY_ID_RESPONSES,
    SLOT_UPDATE_RESPONSES,
)
from src.slots.schemas import TimeSlotCreate, TimeSlotInfo, TimeSlotUpdate
from src.slots.service import slot_service
from src.users.models import User

logger = get_logger(__name__)

router = APIRouter(prefix='/cafes', tags=['Временные слоты'])

SessionDep = Annotated[AsyncSession, Depends(get_async_session)]


@router.post(
    '/{cafe_id}/time_slots',
    response_model=TimeSlotInfo,
    response_model_exclude_none=True,
    description='Новый временной слот в кафе',
    status_code=status.HTTP_201_CREATED,
    responses=SLOT_CREATE_RESPONSES,
)
async def create_new_time_slot(
    session: SessionDep,
    time_slot: TimeSlotCreate,
    cafe_id: uuid.UUID,
    current_user: User = Depends(get_user_by_role(STAFF_ROLE)),
) -> Slot:
    """Создаёт временной слот.

    Доступно для админа и менеджера.

    Raises:
        HTTPException: (400) Если слот пересекается с существующим.
        HTTPException: (403) Если недостаточно прав.

    """
    return await slot_service.create_time_slot(
        session,
        time_slot,
        cafe_id,
        current_user,
    )


@router.patch(
    '/{cafe_id}/time_slots/{slot_id}',
    response_model=TimeSlotInfo,
    response_model_exclude_none=True,
    description='Обновление информации о столе в кафе по его ID.\n'
    'Только для администраторов и менеджеров.',
    status_code=status.HTTP_200_OK,
    responses=SLOT_UPDATE_RESPONSES,
)
async def partially_update_timeslot(
    slot_id: uuid.UUID,
    obj_in: TimeSlotUpdate,
    session: SessionDep,
    cafe_id: uuid.UUID,
    current_user: User = Depends(get_user_by_role(STAFF_ROLE)),
) -> Slot:
    """Частично изменяет проект.

    Доступно Только для администраторов и менеджеров.
    """
    return await slot_service.update_time_slot(
        session,
        slot_id,
        obj_in,
        cafe_id,
        current_user,
    )


@router.get(
    '/{cafe_id}/time_slots',
    response_model=list[TimeSlotInfo],
    response_model_exclude_none=True,
    description='Cписок временных слотов в кафе.',
    status_code=status.HTTP_200_OK,
    responses=SLOTS_LIST_RESPONSES,
)
async def get_all_time_slots(
    session: SessionDep,
    cafe_id: uuid.UUID,
    current_user: User = Depends(get_user_by_role(ALL_ROLE)),
    show_active: bool = Query(
        True,
        description='Показывать только активные слоты',
    ),
) -> list[Slot]:
    """Возвращает список всех временных слотов в кафе.

    - **USER:** show_active принудительно True.
    - **MANAGER/ADMIN:** Видит слоты согласно параметру.
        Если параметр не указан — видит все.
    """
    return await slot_service.get_time_slots(
        session,
        cafe_id,
        current_user,
        show_active,
    )


@router.get(
    '/{cafe_id}/time_slots/{slot_id}',
    response_model=TimeSlotInfo,
    response_model_exclude_none=True,
    description='Информация о временном слоте в кафе по его ID.',
    status_code=status.HTTP_200_OK,
    responses=SLOT_GET_BY_ID_RESPONSES,
)
async def get_time_slot(
    session: SessionDep,
    cafe_id: uuid.UUID,
    slot_id: uuid.UUID,
    current_user: User = Depends(get_user_by_role(ALL_ROLE)),
) -> Optional[Slot]:
    """Возвращает временной слот в кафе по его ID.

    - **USER:** видит только активные слоты.
    - **MANAGER/ADMIN:** видит любые слоты.
    """
    active_only = current_user.role not in STAFF_ROLE
    return await slot_service.get_time_slot_by_id(
        session,
        cafe_id,
        slot_id,
        active_only=active_only,
    )
