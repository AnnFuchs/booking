from datetime import date


def validate_date_not_in_past(value: date) -> date:
    """Выбрасывает ValueError, если дата в прошлом."""
    if value < date.today():
        raise ValueError('Дата бронирования не может быть в прошлом')
    return value
