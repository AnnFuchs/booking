from enum import StrEnum
from pathlib import Path
from typing import Annotated, Union

from pydantic_extra_types.phone_numbers import (
    PhoneNumber,
    PhoneNumberValidator,
)


# Константы аутентификации и управления пользователями
class Role(StrEnum):
    """Роль пользователя в системе."""

    USER = 'USER'
    MANAGER = 'MANAGER'
    ADMIN = 'ADMIN'


JWT_LIFE: int = 3600
TOKEN_TYPE: str = 'Bearer'

# Константы модуля media
BASE_DIR: Path = Path(__file__).resolve().parents[2]
"""Корневая директория проекта."""

MEDIA_DIR: Path = BASE_DIR / 'storage' / 'media'
"""Директория для хранения загруженных изображений."""

MAX_IMAGE_SIZE_BYTES: int = 5 * 1024 * 1024
"""Максимальный допустимый размер изображения: 5 Мб."""

ALLOWED_EXTENSIONS: tuple[str, str, str] = ('.jpg', '.jpeg', '.png')
"""Разрешенные расширения загружаемых изображений."""

ALLOWED_CONTENT_TYPES: tuple[str, str] = ('image/jpeg', 'image/png')
"""Разрешенные content-type для загружаемых изображений."""

JPEG_QUALITY_START: int = 95
"""Начальное качество JPG при сохранении изображения."""

JPEG_QUALITY_MIN: int = 50
"""Минимальное допустимое качество JPG при сжатии."""

JPEG_QUALITY_STEP: int = 5
"""Шаг уменьшения качества JPG при попытке уложиться в лимит размера."""

FILE_NAME_MAX_LENGTH: int = 255
"""Максимальное количество символов в названии файла."""

MIME_TYPE_MAX_LENGTH: int = 50
"""Максимальное количество символов значения типа файла."""

FILE_PATH_MAX_LENGTH: int = 500
"""Максимальное количество символов в полном пути к файлу."""

CHUNK_SIZE: int = 1024 * 1024
"""Размер куска для проверки загружаемого файла допустимому размеру."""

RGB_STANDARD: tuple[int, int, int] = (255, 255, 255)
"""Цветовая палитра изображения."""

ERROR_FILE_NAME_NOT_PROVIDED: str = 'Не передано имя файла.'
"""Сообщение об ошибке, если файл не был передан."""

ERROR_FILE_EMPTY: str = 'Файл пустой.'
"""Сообщение об ошибке, если файл пустой."""

ERROR_FILE_TOO_LARGE: str = 'Размер файла превышает 5 Мб.'
"""Сообщение об ошибке, если размер файла превышает допустимый лимит."""

ERROR_UNSUPPORTED_FILE_TYPE: str = 'Поддерживаются только JPG и PNG.'
"""Сообщение об ошибке, если загружен неподдерживаемый тип файла."""

ERROR_INVALID_CONTENT_TYPE: str = (
    'Неверный content-type. Используйте image/jpeg или image/png.'
)
"""Сообщение об ошибке,
если content-type не соответствует допустимым форматам.
"""

ERROR_FILE_IS_NOT_IMAGE: str = 'Файл не является изображением.'
"""Сообщение об ошибке, если переданный файл не является изображением."""

ERROR_IMAGE_CANNOT_BE_COMPRESSED: str = (
    'Не удалось привести изображение к размеру до 5 Мб.'
)
"""Сообщение об ошибке,
если изображение не удалось ужать до допустимого размера.
"""

ERROR_IMAGE_NOT_FOUND: str = 'Изображение не найдено.'
"""Сообщение об ошибке, если запись об изображении не найдена."""

ERROR_IMAGE_FILE_NOT_FOUND: str = 'Файл изображения не найден на диске.'
"""Сообщение об ошибке, если файл изображения отсутствует на диске."""

ERROR_IMAGE_SAVE_FAILED: str = 'Не удалось сохранить изображение.'
"""Сообщение об ошибке, если не удалось сохранить изображение."""

# Доп константы аутентификации и управления пользователями
TOKEN_FORMAT: str = 'JWT'
STAFF_ROLE: tuple[Role, Role] = (Role.ADMIN, Role.MANAGER)
ALL_ROLE: tuple[Role, Role, Role] = (Role.ADMIN, Role.MANAGER, Role.USER)
ADMIN_ONLY_UPDATE_FIELDS: tuple[str, str] = ('role', 'is_active')

MIN_LENGTH: int = 1
"""Минимальная длина всех обязательных полей."""

NAME_MAX_LENGTH: int = 100
"""Максимальная длина для поля name."""

ADDRESS_MAX_LENGTH: int = 256
"""Максимальная длина для поля address."""

PHONE_MAX_LENGTH: int = 20
"""Максимальная длина для поля phone."""

DESCRIPTION_MAX_LENGTH: int = 500
"""Максимальная длина для поля description."""

MESSAGE_DUPLICATE_NAME_AND_ADDRESS: str = (
    'Кафе с таким названием и адресом уже существует.'
)
"""Сообщение, если связка name + address не уникальна."""

MESSAGE_MANAGERS_ID_IS_NULL: str = 'Список managers_id не может быть пустым.'
"""Сообщение, если предан пустой список managers_id"""

MESSAGE_MANAGERS_ID_DUPLICATE: str = 'Список managers_id содержит дубликаты.'
"""Сообщение, если в списке managers_id находятся дубликаты."""

MESSAGE_CAPACITY_MORE_ONE: str = 'capacity должен быть >= 1.'
"""Сообщение, если в поле capacity передано значение меньше 1."""

MESSAGE_NOT_NULL: str = 'Поле не может быть null.'
"""Сообщение, если в поле переданно null."""
# === Ошибки валидации временных слотов ===
SLOT_OVERLAP_DETECTED: str = 'Выбранный интервал пересекается с другим слотом.'
"""ErrMsg: временной интервал пересекается с существующим слотом."""

SLOT_INVALID_TIME_ORDER: str = 'start_time должно быть меньше end_time'
"""Возвращается когда время начала слота больше или равно времени окончания."""

SLOT_NOT_FOUND: str = 'Временной слот не найден'
"""ErrMsg: запрошенный временной слот отсутствует в системе."""

# === Настройки временных слотов ===
SLOT_DURATION_MINUTES: int = 90
"""Длительность временного слота в минутах.

Используется для расчета доступных интервалов бронирования.
Значение 90 минут оптимально для среднего времени посещения кафе.
"""

# === Форматы данных ===
TIME_FORMAT: str = '%H:%M'
"""Формат времени для API и сериализации.

Пример: '14:30' для 2 часов 30 минут дня.
Соответствует 24-часовому формату без секунд.
"""

# === Пагинация ===
DEFAULT_OFFSET: int = 0
"""Смещение (количество пропускаемых записей) при пагинации по умолчанию."""

DEFAULT_LIMIT: int = 100
"""Лимит (максимальное количество записей) при пагинации по умолчанию."""

# === Ошибки доступа ===
ACCESS_FORBIDDEN_DETAIL: str = 'Недостаточно прав для доступа к этому ресурсу.'
"""ErrMsg: при попытке доступа без необходимых прав доступа."""


class BookingStatus(StrEnum):
    """Статусы бронирования."""

    BOOKING = 'BOOKING'
    """Забронировано."""

    CANCELED = 'CANCELED'
    """Отменено."""

    ACTIVE = 'ACTIVE'
    """Клиент подошел."""

    COMPLETED = 'COMPLETED'
    """Обслуживание завершено."""


MAX_BOOKINGS_PER_USER: int = 3
"""Лимит активных броней на одного человека."""

BOOKING_RESERVATION_TIME_MINUTES: int = 60
"""Длительность слота в минутах."""

MAX_BOOKING_COMMENT: int = 500
"""Максимальная длина комментария к бронированию."""

LOG_FILE_PATH: Path = Path('logs/app.log')
"""Путь к логам."""

LOG_MAX_BYTES: int = 30 * 1024 * 1024
"""Максимальный размер файла логов в байтах."""

LOG_BACKUP_COUNT: int = 3
"""Максимальное число хранимы старых файлов логирования."""

LOG_FORMAT: str = (
    '%(asctime)s | %(levelname)s | %(name)s | %(user_info)s | %(message)s'
)
"""Формат логирования."""

LOG_SYS_NAME: str = 'SYSTEM'
"""Название системы для логгера."""

LOG_DATEFMT: str = '%Y-%m-%d %H:%M:%S'
"""Формат даты и времени для логгера."""

TABLE_SLOT_ADVANCE_DAYS: int = 30
"""Количество дней вперёд для автоматического создания TableSlot."""

DEFAULT_PHONE_REGION: str = 'RU'
"""Дефолтный регион номера телефона."""

E164_RU_NUMBER = Annotated[
    Union[str, PhoneNumber],
    PhoneNumberValidator(
        default_region=DEFAULT_PHONE_REGION,
        number_format='E164',
    ),
]
"""Тип данных для номера телефона в формате E164."""
