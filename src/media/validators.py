from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from src.core.constants import (
    ALLOWED_CONTENT_TYPES,
    ALLOWED_EXTENSIONS,
    ERROR_FILE_EMPTY,
    ERROR_FILE_NAME_NOT_PROVIDED,
    ERROR_FILE_TOO_LARGE,
    ERROR_INVALID_CONTENT_TYPE,
    ERROR_UNSUPPORTED_FILE_TYPE,
    MAX_IMAGE_SIZE_BYTES,
)
from src.core.logger import get_logger

logger = get_logger(__name__)


def validate_file_meta(file: UploadFile) -> None:
    """Проверяет имя файла, расширение и content-type."""
    if file.filename is None:
        logger.warning('Имя файла не передано.')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_FILE_NAME_NOT_PROVIDED,
        )

    suffix = Path(file.filename).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        logger.warning(
            'Передан файл %s с не поддерживаемым разрешением %s.',
            file.filename,
            suffix,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_UNSUPPORTED_FILE_TYPE,
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        logger.warning(
            'Передан файл %s с не поддерживаемым типом %s.',
            file.filename,
            file.content_type,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_INVALID_CONTENT_TYPE,
        )


def validate_file_not_empty(file_bytes: bytes) -> None:
    """Проверяет, что файл не пустой."""
    if not file_bytes:
        logger.warning('Передан пустой файл.')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_FILE_EMPTY,
        )


def validate_chunked_file_size(total_size: int) -> None:
    """Проверяет, что размер файла не превышает допустимый лимит."""
    if total_size > MAX_IMAGE_SIZE_BYTES:
        logger.warning(
            'Передан файл размером %s. Допустимый размер %s.',
            total_size,
            MAX_IMAGE_SIZE_BYTES,
        )
        raise HTTPException(
            status_code=413,
            detail=ERROR_FILE_TOO_LARGE,
        )
