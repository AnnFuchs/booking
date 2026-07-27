import uuid

from pydantic import BaseModel


class MediaUploadResponse(BaseModel):
    """Схема ответа после успешной загрузки изображения."""

    media_id: uuid.UUID
