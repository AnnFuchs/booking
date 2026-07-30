import uuid
from typing import (
    Any,
    Generic,
    Optional,
    Sequence,
    Type,
    TypeVar,
)

from sqlalchemy import and_, select
from sqlalchemy.exc import StatementError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.interfaces import ExecutableOption

from src.core.logger import get_logger
from src.crud.utils import (
    build_filter_conditions,
    check_all_fields_valid,
    check_options_valid,
    validate_and_get_column,
)
from src.db.base import Base

ModelType = TypeVar('ModelType', bound=Base)

logger = get_logger(__name__)


class CRUDBase(Generic[ModelType]):
    """Базовый класс для CRUD операций с моделями SQLAlchemy."""

    def __init__(self, model: Type[ModelType]) -> None:
        """Инициализирует CRUD объект с указанной моделью."""
        self.model: Type[ModelType] = model
        self.available_columns: list[str] = [
            col.name for col in self.model.__table__.columns
        ]

    async def get(
        self,
        session: AsyncSession,
        obj_id: uuid.UUID,
        filters: dict[str, Any] | None = None,
        options: list[ExecutableOption] | None = None,
    ) -> Optional[ModelType]:
        """Получить объект по его id с дополнительной фильтрацией.

        Args:
            session: Асинхронная сессия БД
            obj_id: ID объекта
            filters: Дополнительные фильтры
            options: Список опций загрузки

        Returns:
            Объект модели или None

        Raises:
            AttributeError: Если указано несуществующее поле в фильтрах
            TypeError: Если поле не является колонкой БД
            ValueError: Если оператор не поддерживается

        """
        query = select(self.model).where(self.model.id == obj_id)
        if options:
            options = check_options_valid(options)
            query = query.options(*options) if options is not None else query
        if filters:
            conditions = build_filter_conditions(self.model, filters)
            if conditions:
                query = query.where(and_(*conditions))
        result = await session.execute(query)
        return result.unique().scalar_one_or_none()

    async def get_multi(
        self,
        session: AsyncSession,
        *,
        filters: dict[str, Any] | None = None,
    ) -> Sequence[ModelType]:
        """Получить список объектов с фильтрацией.

        Args:
            session: Асинхронная сессия БД
            filters: Фильтры для выборки

        Returns:
            Список объектов модели

        Raises:
            AttributeError: Если указано несуществующее поле в фильтрах
            TypeError: Если поле не является колонкой БД
            ValueError: Если оператор не поддерживается

        """
        query = select(self.model)
        if filters:
            conditions = build_filter_conditions(self.model, filters)
            if conditions:
                query = query.where(and_(*conditions))
        return (await session.execute(query)).scalars().all()

    async def create(
        self,
        session: AsyncSession,
        obj_in: Any,
        exclude_fields: set[str] | None = None,
        commit: bool = True,
        **extra_data: Any,
    ) -> ModelType:
        """Создать новый объект в БД.

        Args:
            session: Асинхронная сессия БД
            obj_in: Pydantic схема с данными для создания
            exclude_fields: поля, не входящие в схему
            commit: нужно ли осуществлять коммит
            **extra_data: Дополнительные данные в формате field_name=value

        Returns:
            Созданный объект модели

        Raises:
            AttributeError: Если поле в extra_data не существует в модели
            TypeError: Если поле существует, но не является колонкой БД
            ValueError: Если переданы невалидные поля

        """
        _, obj_in_data = check_all_fields_valid(
            self.model,
            obj_in,
            exclude_fields,
            extra_data,
            by_alias=True,
            exclude_unset=None,
        )
        db_obj = self.model(**obj_in_data)
        session.add(db_obj)
        if commit:
            await session.commit()
            await session.refresh(db_obj)
        else:
            await session.flush()
        return db_obj

    async def update(
        self,
        session: AsyncSession,
        db_obj: ModelType,
        obj_in: Any,
        exclude_fields: set[str] | None = None,
    ) -> ModelType:
        """Обновить существующий объект в БД.

        Args:
            session: Асинхронная сессия БД
            db_obj: Объект модели для обновления
            obj_in: Pydantic схема с данными для обновления
                (exclude_unset=True)
            exclude_fields: поля не входящие в схему

        Returns:
            Обновленный объект модели

        Raises:
            AttributeError: Если поле в obj_in не существует в модели
            TypeError: Если поле существует, но не является колонкой БД
            ValueError: Если переданы невалидные поля

        """
        valid_fields, update_data = check_all_fields_valid(
            self.model,
            obj_in,
            exclude_fields,
            extra_data=None,
            by_alias=None,
            exclude_unset=True,
        )
        for field in valid_fields:
            setattr(db_obj, field, update_data[field])
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def get_by_attribute(
        self,
        attr_name: str,
        attr_value: Any,
        session: AsyncSession,
    ) -> Optional[ModelType]:
        """Получить объект по значению указанного атрибута.

        Args:
            attr_name: Имя атрибута модели
            attr_value: Значение атрибута для поиска
            session: Асинхронная сессия БД

        Returns:
            Объект модели или None, если объект не найден

        """
        if not hasattr(self.model, attr_name):
            logger.warning(
                'Атрибут %s не найден в модели %s',
                attr_name,
                self.model.__name__,
            )
            return None

        attr = getattr(self.model, attr_name)
        try:
            result = await session.execute(
                select(self.model).where(attr == attr_value),
            )
            return result.scalars().first()
        except StatementError as e:
            logger.warning(
                'StatementError при поиске по %s=%s в модели %s: %s',
                attr_name,
                attr_value,
                self.model.__name__,
                e,
            )
            return None

    async def get_active_objects_ordered(
        self,
        session: AsyncSession,
        order_by: str = 'created_at',
    ) -> Sequence[ModelType]:
        """Получить все активные объекты с сортировкой.

        Args:
            session: Асинхронная сессия БД
            order_by: Имя поля для сортировки (по умолчанию 'created_at')

        Returns:
            Список активных объектов модели

        Raises:
        При проверке валидности переданного значения order_by:
            AttributeError: Если поле не существует в модели
            TypeError: Если поле существует, но не является колонкой БД
                   (например, является relationship)

        """
        validated_order_by_field = validate_and_get_column(
            self.model,
            order_by,
        )

        query = (
            select(self.model)
            .where(
                self.model.is_active.is_(True),
            )
            .order_by(validated_order_by_field)
        )

        return (await session.execute(query)).scalars().all()
