from typing import Any, Iterable, Type, TypeVar

from sqlalchemy import BinaryExpression
from sqlalchemy.orm import InstrumentedAttribute, class_mapper
from sqlalchemy.orm.interfaces import ExecutableOption
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
    fields: Iterable[str | Any],
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


def check_options_valid(
    options: list[ExecutableOption],
) -> list[ExecutableOption] | None:
    """Проверяет, что переданные опции являются экземплярами ExecutableOption.

    Отфильтровывает невалидные опции. Если после фильтрации список
    оказывается пустым, логирует предупреждение и возвращает None.

    Args:
        options: Список опций загрузки SQLAlchemy.

    Returns:
        Список валидных опций или None, если все опции были отфильтрованы.

    """
    valid_options = [
        opt for opt in options if isinstance(opt, ExecutableOption)
    ]
    if not valid_options:
        logger.warning(
            'Все переданные options были отфильтрованы как невалидные.',
        )
        return None
    return valid_options


def check_all_fields_valid(
    model: Type[ModelType],
    obj_in: Any,
    exclude_fields: set[str] | None = None,
    extra_data: Any = None,
    by_alias: bool | None = None,
    exclude_unset: bool | None = None,
) -> tuple[list[str], Any]:
    """Проверяет, что все переданные поля существуют в модели БД.

    Извлекает данные из Pydantic-схемы с учётом параметров `by_alias`
    и `exclude_unset`, исключает указанные поля, добавляет `extra_data`
    и проверяет все итоговые ключи на принадлежность к колонкам модели.
    Также валидирует сами `exclude_fields`, заменяя их на подмножество
    реально существующих колонок.

    Args:
        model: Модель SQLAlchemy.
        obj_in: Pydantic-схема с данными.
        exclude_fields: Поля, которые нужно исключить из выгрузки.
        extra_data: Дополнительные данные в формате ключ-значение.
        by_alias: Если True, дамп выполняется с использованием алиасов полей.
        exclude_unset: Если True, исключаются поля, не заданные явно.

    Returns:
        Кортеж (valid_fields, obj_in_data), где:
            - valid_fields: список имён полей, прошедших проверку;
            - obj_in_data: словарь данных, готовый для передачи в модель.

    Raises:
        ValueError: Если в итоговых данных обнаружены поля,
            отсутствующие среди колонок модели.

    """
    if exclude_fields:
        valid_exclude_fields, _ = validate_fields_exist(
            model,
            exclude_fields,
        )
        valid_exclude_fields = set(valid_exclude_fields)
    else:
        valid_exclude_fields = set()

    if by_alias:
        obj_in_data = obj_in.model_dump(
            by_alias=by_alias,
            exclude=valid_exclude_fields,
        )
    elif exclude_unset:
        obj_in_data = obj_in.model_dump(
            exclude_unset=exclude_unset,
            exclude=valid_exclude_fields,
        )
    else:
        obj_in_data = obj_in.model_dump(exclude=valid_exclude_fields)

    if extra_data:
        obj_in_data.update(extra_data)

    valid_fields, invalid_fields = validate_fields_exist(
            model,
            obj_in_data,
        )

    if invalid_fields:
        logger.error(
            'Несуществующие поля %s в модели %s.',
            invalid_fields,
            model.__name__,
        )
        raise ValueError(
            f'Несуществующие поля в модели {model.__name__}: '
            f'{", ".join(invalid_fields)}. '
            f'Доступные поля: {
                ", ".join(
                    sorted(
                        [col.name for col in model.__table__.columns]
                    ),
                ),
            }',
        )

    return valid_fields, obj_in_data
