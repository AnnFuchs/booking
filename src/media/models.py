from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.constants import (
    FILE_PATH_MAX_LEN,
)
from src.db.base import Base


class Media(Base):
    """Модель для хранения информации об изображениях."""

    __tablename__ = 'media'
    __table_args__ = (
        Index('ix_media_is_active', 'is_active'),
        Index('ix_media_created_at', 'created_at'),
    )

    file_path: Mapped[str] = mapped_column(
        String(FILE_PATH_MAX_LEN),
        nullable=False,
        unique=True,
    )
