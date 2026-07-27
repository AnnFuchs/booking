from typing import Any, Type, TypeVar

from sqlalchemy import BinaryExpression
from sqlalchemy.orm import InstrumentedAttribute, class_mapper
from sqlalchemy.orm.properties import RelationshipProperty
from sqlalchemy.sql.elements import ColumnElement

from src.core.logger import get_logger
from src.db.base import Base

ModelType = TypeVar('ModelType', bound=Base)

logger = get_logger(__name__)


def validate_and_get_column(
    model: Type[ModelType],
    field_name: str,
) -> ColumnElement | InstrumentedAttribute:
    """Проверяет существование поля в модели и что оно является колонкой БД.

    ВАЖНО: Возвращает только объекты Column, которые можно использовать
    в WHERE, ORDER BY и других SQL выражениях.

    Args:
        model: Модель SQLAlchemy
        field_name: Имя поля для проверки

    Returns:
        SQLAlchemy Column объект, пригодный для использования
        в SQL выражениях (WHERE, ORDER BY и др.)

    Raises:
        AttributeError: Если поле не существует в модели
        TypeError: Если поле существует, но не является колонкой БД
                   (например, является relationship)

    """
    mapper = class_mapper(model)

    if field_name not in mapper.columns:
        available_columns = sorted(mapper.columns.keys())

        if field_name in {p.key for p in mapper.iterate_properties}:
            prop = mapper.get_property(field_name)
            if isinstance(prop, RelationshipProperty):
                raise TypeError(
                    f'Поле "{field_name}" в модели {model.__name__} '
                    f'является relationship, а не колонкой БД. '
                    f'Доступные колонки: {", ".join(available_columns)}',
                )

        raise AttributeError(
            f'Поле "{field_name}" не найдено в модели {model.__name__}. '
            f'Доступные колонки: {", ".join(available_columns)}',
        )

    return getattr(model, field_name)


def build_filter_conditions(
    model: Type[ModelType],
    filters: dict[str, Any],
) -> list[BinaryExpression]:
    """Преобразует словарь фильтров в список SQLAlchemy условий.

    Поддерживает:
        - field: равенство (field == value)
        - field__gt: больше (field > value)
        - field__lt: меньше (field < value)
        - field__in: в списке (field IN value)
        - field__is_null: IS NULL (значение игнорируется)

    Примеры:
        filters = {
            'age__gt': 18,              # age > 18
            'status__in': [1, 2, 3],    # status IN (1, 2, 3)
            'name__like': 'John%',      # name LIKE 'John%'
            'deleted_at__is_null': True # deleted_at IS NULL
        }

    Args:
        model: Класс модели SQLAlchemy.
        filters: Словарь с условиями фильтрации.

    Returns:
        Список объектов BinaryExpression, готовых для передачи
        в query.filter(*conditions).

    Raises:
        AttributeError: Если поле не существует в модели.
        TypeError: Если поле существует, но не является колонкой БД.
        ValueError: Если оператор не поддерживается.

    """
    conditions = []

    for key, value in filters.items():
        if key.endswith('__is_null'):
            field_name = key[: -len('__is_null')]
            column = validate_and_get_column(model, field_name)
            conditions.append(column.is_(None))
            continue

        if '__' in key:
            field_name, operator = key.split('__', 1)
        else:
            field_name, operator = key, 'eq'

        column = validate_and_get_column(model, field_name)

        if operator == 'eq':
            conditions.append(column == value)
        elif operator == 'gt':
            conditions.append(column > value)
        elif operator == 'lt':
            conditions.append(column < value)
        elif operator == 'in':
            conditions.append(column.in_(value))
        else:
            logger.warning(
                'Неподдерживаемый оператор %s '
                'при формировании списка фильтров.',
                operator,
            )
            raise ValueError(f'Неподдерживаемый оператор: {operator}')

    return conditions


def validate_fields_exist(
    model: Type[ModelType],
    fields: dict[str, Any],
) -> tuple[list[str], list[str]]:
    """Проверяет существование полей в модели.

    Args:
        model: Модель SQLAlchemy
        fields: Словарь полей для проверки

    Returns:
        Кортеж (валидные, невалидные_поля)

    """
    valid_fields = []
    invalid_fields = []

    for field_name in fields:
        try:
            validate_and_get_column(model, field_name)
            valid_fields.append(field_name)
        except (AttributeError, TypeError):
            invalid_fields.append(field_name)

    return valid_fields, invalid_fields
