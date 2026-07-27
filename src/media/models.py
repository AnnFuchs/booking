from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.constants import (
    FILE_PATH_MAX_LENGTH,
)
from src.db.base import Base


class Media(Base):
    """Модель для хранения информации об изображениях."""

    __tablename__ = 'media'

    file_path: Mapped[str] = mapped_column(
        String(FILE_PATH_MAX_LENGTH),
        nullable=False,
        unique=True,
    )
