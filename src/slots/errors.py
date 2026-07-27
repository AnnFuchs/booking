"""Ошибки для модуля временных слотов."""

from src.core.constants import SLOT_OVERLAP_DETECTED


class SlotError(ValueError):
    """Базовое исключение для слотов."""


class SlotOverlapError(SlotError):
    """Слот пересекается с существующим."""

    def __init__(self, detail: str = SLOT_OVERLAP_DETECTED) -> None:
        """Инициализация ошибки пересечения слотов."""
        self.detail = detail
        super().__init__(detail)


class SlotNotFoundError(SlotError):
    """Слот не найден."""

    def __init__(self, slot_id: str) -> None:
        """Инициализация ошибки отсутствия слота."""
        self.slot_id = slot_id
        super().__init__(f'Слот с id {slot_id} не найден')


class SlotAccessDeniedError(SlotError):
    """Нет доступа к слоту."""

    def __init__(self, user_id: str, slot_id: str) -> None:
        """Инициализация ошибки доступа к слоту."""
        self.user_id = user_id
        self.slot_id = slot_id
        super().__init__(
            f'Пользователь {user_id} не имеет доступа к слоту {slot_id}',
        )
