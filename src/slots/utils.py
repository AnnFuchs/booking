from datetime import time

from src.core.constants import SLOT_INVALID_TIME_ORDER


def validate_slot_time(start_time: time, end_time: time) -> None:
    """Выбрасывает ValueError, если время начала позже времени конца."""
    if end_time <= start_time:
        raise ValueError(SLOT_INVALID_TIME_ORDER)
