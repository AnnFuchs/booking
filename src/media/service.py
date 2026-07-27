import uuid
from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from anyio.to_thread import run_sync
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from src.core.constants import (
    CHUNK_SIZE,
    ERROR_FILE_IS_NOT_IMAGE,
    ERROR_IMAGE_CANNOT_BE_COMPRESSED,
    ERROR_IMAGE_FILE_NOT_FOUND,
    ERROR_IMAGE_NOT_FOUND,
    ERROR_IMAGE_SAVE_FAILED,
    JPEG_QUALITY_MIN,
    JPEG_QUALITY_START,
    JPEG_QUALITY_STEP,
    MAX_IMAGE_SIZE_BYTES,
    MEDIA_DIR,
    RGB_STANDARD,
)
from src.core.logger import get_logger
from src.media.models import Media
from src.media.validators import (
    validate_chunked_file_size,
    validate_file_meta,
    validate_file_not_empty,
)

logger = get_logger(__name__)


class MediaService:
    """Сервис для загрузки, обработки и сохранения медиафайлов."""

    async def save_media(
        self,
        session: AsyncSession,
        file: UploadFile,
    ) -> uuid.UUID:
        """Проверяет файл, конвертирует его в JPG и сохраняет."""
        validate_file_meta(file)

        logger.debug(
            'Файл %s проверен, передан для фрагментирования.',
            file.filename,
        )

        chunks = []
        total_size = 0
        chunk_size = CHUNK_SIZE

        while chunk := await file.read(chunk_size):
            total_size += len(chunk)
            validate_chunked_file_size(total_size)
            chunks.append(chunk)

        file_bytes = b''.join(chunks)
        validate_file_not_empty(file_bytes)

        jpeg_bytes = await run_sync(
            self._convert_to_jpeg,
            file_bytes,
        )

        media_id = uuid7()
        MEDIA_DIR.mkdir(parents=True, exist_ok=True)

        file_path = MEDIA_DIR / f'{media_id}.jpg'
        file_path.write_bytes(jpeg_bytes)

        media = Media(id=media_id, file_path=str(file_path))

        try:
            logger.debug(
                'Файл %s передан для записи в базу данных.',
                file.filename,
            )
            session.add(media)
            await session.commit()
            await session.refresh(media)
        except Exception as e:
            logger.error(
                'Возникла ошибка %s при записи файла %s в базу данных.',
                e,
                file.filename,
                exc_info=True,
            )
            await session.rollback()

            if file_path.exists():
                file_path.unlink()
                logger.debug(
                    'Файл %s удалён после ошибки записи в БД.',
                    file_path,
                )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ERROR_IMAGE_SAVE_FAILED,
            )
        logger.debug(
            'Медиа %s успешно сохранено, id=%s.',
            file.filename,
            media.id,
        )
        return media.id

    async def get_media_path(
        self,
        session: AsyncSession,
        media_id: uuid.UUID,
    ) -> Path:
        """Возвращает путь к изображению по его идентификатору."""
        query = select(Media).where(
            Media.id == media_id,
            Media.is_active.is_(True),
        )
        result = await session.execute(query)
        media = result.scalar_one_or_none()

        if media is None:
            logger.warning('Медиа с id %s не обнаружено.', media_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ERROR_IMAGE_NOT_FOUND,
            )

        file_path = Path(media.file_path)

        if not file_path.exists():  # noqa: ASYNC240
            logger.warning(
                'Медиа с id %s не обнаружено по пути %s.',
                media_id,
                file_path,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ERROR_IMAGE_FILE_NOT_FOUND,
            )

        logger.debug('Получен путь %s к файлу %s', file_path, media_id)
        return file_path

    def _convert_to_jpeg(self, file_bytes: bytes) -> bytes:
        """Открывает изображение.

        Переводит его в JPG и возвращает байты файла.
        """
        try:
            image = Image.open(BytesIO(file_bytes))
        except UnidentifiedImageError:
            logger.warning('Переданный файл не является изображением.')
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_FILE_IS_NOT_IMAGE,
            )

        if image.mode in ('RGBA', 'LA') or (
            image.mode == 'P' and 'transparency' in image.info
        ):
            rgba_image = image.convert('RGBA')
            background = Image.new('RGB', rgba_image.size, RGB_STANDARD)
            background.paste(rgba_image, mask=rgba_image.split()[-1])
            image = background
        else:
            image = image.convert('RGB')

        quality = JPEG_QUALITY_START

        while quality >= JPEG_QUALITY_MIN:
            output = BytesIO()
            image.save(
                output,
                format='JPEG',
                quality=quality,
                optimize=True,
            )
            jpeg_bytes = output.getvalue()

            if len(jpeg_bytes) <= MAX_IMAGE_SIZE_BYTES:
                logger.debug(
                    'Изображение сконвертировано в JPEG, '
                    'размер=%d байт, качество=%s.',
                    len(jpeg_bytes),
                    quality,
                )
                return jpeg_bytes

            quality -= JPEG_QUALITY_STEP

        logger.warning('Невозможно сжать изображение до допустимого размера.')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_IMAGE_CANNOT_BE_COMPRESSED,
        )


media_service = MediaService()
