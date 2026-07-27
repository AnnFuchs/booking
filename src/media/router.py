import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_user_by_role
from src.core.constants import STAFF_ROLE
from src.db.session import get_async_session
from src.media.schemas import MediaUploadResponse
from src.media.service import media_service

router = APIRouter(prefix='/media', tags=['Media'])

SessionDep = Annotated[AsyncSession, Depends(get_async_session)]


@router.post(
    '',
    response_model=MediaUploadResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_user_by_role(STAFF_ROLE))],
)
async def upload_image(
    session: SessionDep,
    file: UploadFile = File(...),
) -> MediaUploadResponse:
    """Загружает изображение и возвращает его идентификатор."""
    media_id = await media_service.save_media(session=session, file=file)
    return MediaUploadResponse(media_id=media_id)


@router.get(
    '/{media_id}',
    response_class=FileResponse,
    responses={
        200: {
            'content': {'image/jpeg': {}},
            'description': 'Изображение в бинарном формате.',
        },
    },
)
async def get_image(
    media_id: uuid.UUID,
    session: SessionDep,
) -> FileResponse:
    """Возвращает изображение по его идентификатору."""
    file_path = await media_service.get_media_path(
        session=session,
        media_id=media_id,
    )

    return FileResponse(
        path=file_path,
        media_type='image/jpeg',
        filename=f'{media_id}.jpg',
        content_disposition_type='inline',
    )
