from io import BytesIO
from pathlib import Path
from uuid import UUID

import anyio
import pytest
from PIL import Image
from httpx import AsyncClient
from pytest import MonkeyPatch
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.db.models_for_alembic import Media
from src.media import service as media_service_module

MEDIA_URL = '/media'


def create_image_bytes(
    image_format: str = 'PNG',
    size: tuple[int, int] = (100, 100),
) -> bytes:
    """Создает тестовое изображение в памяти."""
    image = Image.new('RGB', size, (255, 0, 0))
    buffer = BytesIO()
    image.save(buffer, format=image_format)
    return buffer.getvalue()


@pytest.mark.asyncio(loop_scope='session')
class TestMediaAPI:
    """Тесты для API работы с изображениями."""

    async def test_upload_media_by_admin_success(
        self,
        async_client: AsyncClient,
        admin_headers: dict[str, str],
        session: AsyncSession,
        tmp_path: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """Проверка успешной загрузки изображения администратором."""
        monkeypatch.setattr(media_service_module, 'MEDIA_DIR', tmp_path)

        file_bytes = create_image_bytes('PNG')
        response = await async_client.post(
            MEDIA_URL,
            files={'file': ('test.png', file_bytes, 'image/png')},
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert 'media_id' in data

        media_id = UUID(data['media_id'])
        media = await session.get(Media, media_id)

        assert media is not None
        path = anyio.Path(media.file_path)
        assert await path.exists()
        assert Path(media.file_path).suffix == '.jpg'

    async def test_upload_media_by_manager_success(
        self,
        async_client: AsyncClient,
        manager_headers: dict[str, str],
        tmp_path: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """Проверка успешной загрузки изображения менеджером."""
        monkeypatch.setattr(media_service_module, 'MEDIA_DIR', tmp_path)

        file_bytes = create_image_bytes('JPEG')
        response = await async_client.post(
            MEDIA_URL,
            files={'file': ('test.jpg', file_bytes, 'image/jpeg')},
            headers=manager_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert 'media_id' in response.json()

    async def test_upload_media_forbidden_for_user(
        self,
        async_client: AsyncClient,
        user_headers: dict[str, str],
        tmp_path: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """Проверка загрузки изображения обычным пользователем."""
        monkeypatch.setattr(media_service_module, 'MEDIA_DIR', tmp_path)

        file_bytes = create_image_bytes('PNG')
        response = await async_client.post(
            MEDIA_URL,
            files={'file': ('test.png', file_bytes, 'image/png')},
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_upload_media_unauthorized_without_token(
        self,
        async_client: AsyncClient,
        tmp_path: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """Проверка, что без авторизации загрузка недоступна."""
        monkeypatch.setattr(media_service_module, 'MEDIA_DIR', tmp_path)

        file_bytes = create_image_bytes('PNG')
        response = await async_client.post(
            MEDIA_URL,
            files={'file': ('test.png', file_bytes, 'image/png')},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_upload_media_invalid_extension(
        self,
        async_client: AsyncClient,
        admin_headers: dict[str, str],
        tmp_path: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """Проверка ошибки при неподдерживаемом расширении файла."""
        monkeypatch.setattr(media_service_module, 'MEDIA_DIR', tmp_path)

        response = await async_client.post(
            MEDIA_URL,
            files={'file': ('test.txt', b'hello', 'text/plain')},
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_upload_media_too_large(
        self,
        async_client: AsyncClient,
        admin_headers: dict[str, str],
        tmp_path: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """Проверка ошибки при превышении максимального размера файла."""
        monkeypatch.setattr(media_service_module, 'MEDIA_DIR', tmp_path)

        large_bytes = b'a' * (5 * 1024 * 1024 + 1)
        response = await async_client.post(
            MEDIA_URL,
            files={'file': ('big.jpg', large_bytes, 'image/jpeg')},
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_413_CONTENT_TOO_LARGE

    async def test_get_media_success(
        self,
        async_client: AsyncClient,
        admin_headers: dict[str, str],
        tmp_path: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """Проверка успешного получения изображения по media_id."""
        monkeypatch.setattr(media_service_module, 'MEDIA_DIR', tmp_path)

        file_bytes = create_image_bytes('PNG')
        upload_response = await async_client.post(
            MEDIA_URL,
            files={'file': ('test.png', file_bytes, 'image/png')},
            headers=admin_headers,
        )

        assert upload_response.status_code == status.HTTP_201_CREATED
        media_id = upload_response.json()['media_id']

        get_response = await async_client.get(f'{MEDIA_URL}/{media_id}')

        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.headers['content-type'] == 'image/jpeg'
        assert get_response.content.startswith(b'\xff\xd8')

    async def test_get_media_not_found(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Проверка ошибки при запросе несуществующего изображения."""
        response = await async_client.get(
            f'{MEDIA_URL}/01964d4f-1234-7abc-89ab-1234567890ab',
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
