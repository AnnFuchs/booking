class SlotOverlapError(Exception):
    """Слот пересекается с существующим."""

    pass


class SlotTimeOrderError(Exception):
    """Неверный порядок времени начала и конца слота."""

    pass
