class SlotOverlapError(Exception):
    """Слот пересекается с существующим."""

    pass


class SlotNotFoundError(Exception):
    """Слот не найден."""

    pass


class SlotAccessDeniedError(Exception):
    """Нет доступа к слоту."""

    pass
