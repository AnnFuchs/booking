from datetime import date, time, timedelta
from typing import Awaitable, Callable

import pytest
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from src.bookings.models import TableSlot
from src.core.constants import Role
from src.db.models_for_alembic import Cafe, Slot, Table, User

fake = Faker()


@pytest.fixture
async def test_cafe(
    session: AsyncSession,
    create_user: Callable[..., Awaitable[User]],
) -> Cafe:
    """Создает кафе."""
    # 1. Создаем менеджера (create_user вернет объект с UUID id)
    manager = await create_user(role=Role.MANAGER)

    unique_id = uuid7()

    # 2. Создаем кафе
    cafe = Cafe(
        id=unique_id,
        name=f'Кафе {fake.company()}',
        address=fake.address(),
        phone='+79991234567',
        description='Описание кафе.',
        is_active=True,
    )

    session.add(cafe)
    await session.flush()

    manager.cafe_id = cafe.id
    session.add(manager)
    await session.flush()

    await session.commit()
    await session.refresh(cafe)
    return cafe


@pytest.fixture
async def test_table(session: AsyncSession, test_cafe: Cafe) -> Table:
    """Создает стол."""
    table = Table(
        cafe_id=test_cafe.id,
        description='Описание самого стола.',
        seat_number=4,
        is_active=True,
    )
    session.add(table)
    await session.commit()
    await session.refresh(table)
    return table


@pytest.fixture
async def test_table_2(session: AsyncSession, test_cafe: Cafe) -> Table:
    """Создает второй стол в том же кафе."""
    table = Table(
        cafe_id=test_cafe.id,
        description='Описание второго стола.',
        seat_number=2,
        is_active=True,
    )
    session.add(table)
    await session.commit()
    await session.refresh(table)
    return table


@pytest.fixture
async def test_slot(session: AsyncSession, test_cafe: Cafe) -> Slot:
    """Создает временной слот."""
    slot = Slot(
        start_time=time(18, 0),
        end_time=time(20, 0),
        description='Описание слота',
        cafe_id=test_cafe.id,
        is_active=True,
    )
    session.add(slot)
    await session.commit()
    await session.refresh(slot)
    return slot


@pytest.fixture
async def test_table_slot(
    session: AsyncSession,
    test_table: Table,
    test_slot: Slot,
) -> TableSlot:
    """Создает связку стола и слота на конкретную дату."""
    ts = TableSlot(
        table_id=test_table.id,
        slot_id=test_slot.id,
        booking_date=date.today() + timedelta(days=1),
        is_active=True,
        booking_id=None,
    )
    session.add(ts)
    await session.commit()
    await session.refresh(ts)
    return ts


@pytest.fixture
async def test_table_slot_2(
    session: AsyncSession,
    test_table_2: Table,
    test_slot: Slot,
) -> TableSlot:
    """Создает ВТОРУЮ связку (другой стол, то же время)."""
    ts = TableSlot(
        table_id=test_table_2.id,
        slot_id=test_slot.id,
        booking_date=date.today() + timedelta(days=1),
        is_active=True,
        booking_id=None,
    )
    session.add(ts)
    await session.commit()
    await session.refresh(ts)
    return ts
