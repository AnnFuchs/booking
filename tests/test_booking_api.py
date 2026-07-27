from datetime import date, timedelta
from typing import Awaitable, Callable

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from starlette import status

from src.auth.jwt import create_access_token
from src.bookings.models import TableSlot
from src.core.constants import MAX_BOOKING_COMMENT, Role
from src.db.models_for_alembic import Booking, User

BOOKING_URL = '/booking'


@pytest.mark.asyncio(loop_scope='session')
class TestBookingAPI:
    """Тесты для API бронирования."""

    async def test_create_booking_success(
        self,
        async_client: AsyncClient,
        user_headers: dict[str, str],
        test_cafe: any,
        test_table_slot: any,
        session: any,
    ) -> None:
        """Проверка успешного создания бронирования."""
        payload = {
            'cafe_id': str(test_cafe.id),
            'tables_slots': [
                {
                    'table_id': str(test_table_slot.table_id),
                    'slot_id': str(test_table_slot.slot_id),
                },
            ],
            'guest_number': 2,
            'booking_date': str(test_table_slot.booking_date),
            'note': 'Тестовое бронирование',
        }

        response = await async_client.post(
            BOOKING_URL,
            json=payload,
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['cafe']['id'] == str(test_cafe.id)

    async def test_get_booking_details_success(
        self,
        async_client: AsyncClient,
        user_headers: dict[str, str],
        test_cafe: any,
        test_table_slot: any,
        session: any,
    ) -> None:
        """Проверка получения деталей бронирования по ID."""
        # 1. Создаем бронь
        payload = {
            'cafe_id': str(test_cafe.id),
            'tables_slots': [
                {
                    'table_id': str(test_table_slot.table_id),
                    'slot_id': str(test_table_slot.slot_id),
                },
            ],
            'guest_number': 2,
            'booking_date': str(test_table_slot.booking_date),
            'note': 'Поиск деталей',
        }

        res_create = await async_client.post(
            BOOKING_URL,
            json=payload,
            headers=user_headers,
        )
        booking_id = res_create.json()['id']

        # 2. Получаем детали по созданному ID
        response = await async_client.get(
            f'{BOOKING_URL}/{booking_id}',
            headers=user_headers,
        )

        # 3. Проверки
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['id'] == booking_id
        assert data['cafe']['id'] == str(test_cafe.id)
        assert len(data['tables_slots']) == 1

    async def test_create_booking_limit_check(
        self,
        async_client: AsyncClient,
        user_headers: dict[str, str],
        test_cafe: any,
        test_table: any,
        test_slot: any,
        session: any,
    ) -> None:
        """Проверка лимита 3 бронирования (бизнес-логика)."""
        from datetime import date, timedelta

        # Создаем 3 брони
        for i in range(3):
            ts = TableSlot(
                table_id=test_table.id,
                slot_id=test_slot.id,
                booking_date=date.today() + timedelta(days=i + 1),
                is_active=True,
            )
            session.add(ts)
            await session.commit()

            p = {
                'cafe_id': str(test_cafe.id),
                'guest_number': 1,
                'booking_date': str(ts.booking_date),
                'tables_slots': [
                    {'table_id': str(ts.table_id), 'slot_id': str(ts.slot_id)},
                ],
            }
            await async_client.post(BOOKING_URL, json=p, headers=user_headers)
        # Делаем 3 успешных запроса
        for _ in range(3):
            await async_client.post(BOOKING_URL, json=p, headers=user_headers)
        # 4-я попытка
        res = await async_client.post(
            BOOKING_URL,
            json=p,
            headers=user_headers,
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    async def test_booking_soft_delete(
        self,
        async_client: AsyncClient,
        user_headers: dict[str, str],
        test_cafe: any,
        test_table_slot: any,
        session: any,
    ) -> None:
        """Проверяет логику мягкого удаления."""
        # 1. Создаем бронь
        payload = {
            'cafe_id': str(test_cafe.id),
            'tables_slots': [
                {
                    'table_id': str(test_table_slot.table_id),
                    'slot_id': str(test_table_slot.slot_id),
                },
            ],
            'guest_number': 2,
            'booking_date': str(test_table_slot.booking_date),
        }
        res = await async_client.post(
            BOOKING_URL,
            json=payload,
            headers=user_headers,
        )
        booking_id = res.json()['id']

        # 2. Удаляем (вызываем эндпоинт отмены)
        res = await async_client.patch(
            f'{BOOKING_URL}/{booking_id}',
            json={'status': 'CANCELED'},
            headers=user_headers,
        )

        assert res.status_code == status.HTTP_200_OK

        data = res.json()
        assert data['is_active'] is False
        assert data['status'] == 'CANCELED'

        # 3. Проверяем, что в БД запись физически осталась
        query = select(Booking).where(Booking.id == booking_id)
        result = await session.execute(query)
        db_booking = result.scalar_one_or_none()
        assert db_booking is not None  # Запись всё еще в базе
        assert db_booking.is_active is False  # Но она деактивирована

    # --- Негативные сценарии ---

    async def test_booking_past_date_error(
        self,
        async_client: AsyncClient,
        user_headers: dict[str, str],
        test_cafe: any,
        test_table_slot: any,
    ) -> None:
        """Проверка валидатора: нельзя бронировать на вчера."""
        from datetime import date, timedelta

        payload = {
            'cafe_id': str(test_cafe.id),
            'guest_number': 1,
            'booking_date': str(date.today() - timedelta(days=1)),
            'tables_slots': [
                {
                    'table_id': str(test_table_slot.table_id),
                    'slot_id': str(test_table_slot.slot_id),
                },
            ],
        }
        response = await async_client.post(
            BOOKING_URL,
            json=payload,
            headers=user_headers,
        )

        # Здесь должен быть либо 400, либо 422
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_CONTENT,
        ]

    async def test_booking_note_too_long(
        self,
        async_client: AsyncClient,
        user_headers: dict[str, str],
        test_cafe: any,
        test_table_slot: any,
    ) -> None:
        """Проверка лимита символов в комментарии."""
        payload = {
            'cafe_id': str(test_cafe.id),
            'guest_number': 1,
            'booking_date': str(test_table_slot.booking_date),
            'note': 'a' * (MAX_BOOKING_COMMENT + 1),
            'tables_slots': [
                {
                    'table_id': str(test_table_slot.table_id),
                    'slot_id': str(test_table_slot.slot_id),
                },
            ],
        }
        response = await async_client.post(
            BOOKING_URL,
            json=payload,
            headers=user_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    async def test_booking_empty_tables_error(
        self,
        async_client: AsyncClient,
        user_headers: dict[str, str],
        test_cafe: any,
    ) -> None:
        """Проверка: нельзя забронировать ничего."""
        payload = {
            'cafe_id': str(test_cafe.id),
            'guest_number': 1,
            'booking_date': str(date.today()),
            'tables_slots': [],
        }
        response = await async_client.post(
            BOOKING_URL,
            json=payload,
            headers=user_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    async def test_booking_required_fields(
        self,
        async_client: AsyncClient,
        user_headers: dict[str, str],
    ) -> None:
        """Проверка, что нельзя отправить пустой запрос."""
        response = await async_client.post(
            BOOKING_URL,
            json={},
            headers=user_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    async def test_update_status_cancel(
        self,
        async_client: AsyncClient,
        user_headers: dict[str, str],
        test_cafe: any,
        test_table_slot: any,
    ) -> None:
        """Закрываем логику отмены в методе update."""
        p = {
            'cafe_id': str(test_cafe.id),
            'guest_number': 1,
            'booking_date': str(test_table_slot.booking_date),
            'tables_slots': [
                {
                    'table_id': str(test_table_slot.table_id),
                    'slot_id': str(test_table_slot.slot_id),
                },
            ],
        }
        res = await async_client.post(
            BOOKING_URL,
            json=p,
            headers=user_headers,
        )
        b_id = res.json()['id']

        # Меняем статус на CANCELED
        response = await async_client.patch(
            f'{BOOKING_URL}/{b_id}',
            json={'status': 'CANCELED'},
            headers=user_headers,
        )
        assert response.status_code == status.HTTP_200_OK

    async def test_update_booking_simple_fields(
        self,
        async_client: AsyncClient,
        user_headers: dict[str, str],
        test_cafe: any,
        test_table_slot: any,
    ) -> None:
        """Проверка обновления полей."""
        # 1. Создаем бронь
        p = {
            'cafe_id': str(test_cafe.id),
            'guest_number': 1,
            'booking_date': str(test_table_slot.booking_date),
            'tables_slots': [
                {
                    'table_id': str(test_table_slot.table_id),
                    'slot_id': str(test_table_slot.slot_id),
                },
            ],
        }
        res = await async_client.post(
            BOOKING_URL,
            json=p,
            headers=user_headers,
        )
        b_id = res.json()['id']

        # 2. Обновляем только количество гостей
        payload = {'guest_number': 5, 'note': 'Изменили количество мест'}
        response = await async_client.patch(
            f'{BOOKING_URL}/{b_id}',
            json=payload,
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['guest_number'] == 5

    async def test_create_booking_conflict(
        self,
        async_client: AsyncClient,
        user_headers: dict[str, str],
        test_cafe: any,
        test_table_slot: any,
    ) -> None:
        """Сценарий: Запрет повторного бронирования того же слота."""
        payload = {
            'cafe_id': str(test_cafe.id),
            'tables_slots': [
                {
                    'table_id': str(test_table_slot.table_id),
                    'slot_id': str(test_table_slot.slot_id),
                },
            ],
            'guest_number': 2,
            'booking_date': str(test_table_slot.booking_date),
        }
        # Бронируем первый раз
        await async_client.post(
            BOOKING_URL,
            json=payload,
            headers=user_headers,
        )

        # Пытаемся забронировать второй раз
        response = await async_client.post(
            BOOKING_URL,
            json=payload,
            headers=user_headers,
        )

        # Проверяем только статус
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_manager_cannot_cancel_other_cafe_booking(
        self,
        async_client: AsyncClient,
        user_headers: dict[str, str],
        create_user: Callable[..., Awaitable[User]],
        test_cafe: any,
        test_table_slot: any,
    ) -> None:
        """Сценарий: Менеджер другого кафе не может отменить чужую бронь."""
        # 1. Создаем бронь обычным юзером
        payload = {
            'cafe_id': str(test_cafe.id),
            'tables_slots': [
                {
                    'table_id': str(test_table_slot.table_id),
                    'slot_id': str(test_table_slot.slot_id),
                },
            ],
            'guest_number': 2,
            'booking_date': str(test_table_slot.booking_date),
        }
        res = await async_client.post(
            BOOKING_URL,
            json=payload,
            headers=user_headers,
        )
        booking_id = res.json()['id']

        # 2. Создаем менеджера без привязки к кафе
        other_manager = await create_user(role=Role.MANAGER, cafe_id=None)
        token = create_access_token(data={'sub': str(other_manager.id)})

        # 3. Менеджер пытается отменить через PATCH
        response = await async_client.patch(
            f'{BOOKING_URL}/{booking_id}',
            json={'status': 'CANCELED'},
            headers={'Authorization': f'Bearer {token}'},
        )
        # Ожидаем 403 или 404
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ]

    async def test_create_booking_in_past_forbidden(
        self,
        async_client: AsyncClient,
        user_headers: dict[str, str],
        test_cafe: any,
        test_table_slot: any,
    ) -> None:
        """Сценарий: Запрет бронирования на вчерашнее число."""
        payload = {
            'cafe_id': str(test_cafe.id),
            'tables_slots': [
                {
                    'table_id': str(test_table_slot.table_id),
                    'slot_id': str(test_table_slot.slot_id),
                },
            ],
            'guest_number': 2,
            'booking_date': str(date.today() - timedelta(days=1)),  # Вчера
        }
        response = await async_client.post(
            BOOKING_URL,
            json=payload,
            headers=user_headers,
        )

        # Ожидаем 422
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    async def test_create_booking_user_conflict_error(
        self,
        async_client: AsyncClient,
        user_headers: dict[str, str],
        test_cafe: any,
        test_table_slot: any,
        test_table_slot_2: any,
        session: any,
    ) -> None:
        """Проверка: нельзя забронировать два кафе на одно время."""
        # 1. Создаем первую бронь
        payload1 = {
            'cafe_id': str(test_cafe.id),
            'guest_number': 2,
            'booking_date': str(test_table_slot.booking_date),
            'tables_slots': [
                {
                    'table_id': str(test_table_slot.table_id),
                    'slot_id': str(test_table_slot.slot_id),
                },
            ],
        }
        res1 = await async_client.post(
            BOOKING_URL,
            json=payload1,
            headers=user_headers,
        )
        assert res1.status_code == status.HTTP_201_CREATED

        # 2. Пытаемся создать вторую бронь на то же время на другой стол
        payload2 = {
            'cafe_id': str(test_cafe.id),
            'guest_number': 1,
            'booking_date': str(test_table_slot.booking_date),
            'tables_slots': [
                {
                    'table_id': str(
                        test_table_slot_2.table_id,
                    ),
                    'slot_id': str(test_table_slot.slot_id),
                },
            ],
        }
        res2 = await async_client.post(
            BOOKING_URL,
            json=payload2,
            headers=user_headers,
        )

        # 3. Теперь должна сработать проверка пользователя
        assert res2.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            res2.json()['detail']
            == 'У вас уже есть бронь на это время в другом заведении'
        )
