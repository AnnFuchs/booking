from src.core.constants import (
    MESSAGE_DUPLICATE_NAME_AND_ADDRESS,
    MESSAGE_MANAGERS_ID_DUPLICATE,
    MESSAGE_MANAGERS_ID_IS_NULL,
)


class CafeError(ValueError):
    """Базовое исключение для всех ошибок кафе.

    Позволяет ловить ВСЕ ошибки слотов одной строкой:
        try:
            # какой-то код с кафе
            await cafe_service.create_cafe(...)
        except CafeError as error:  # Ловит ЛЮБУЮ ошибку из модуля cafe
            # Обработка любой ошибки кафе
            print(f"Ошибка в модуле кафе: {error}")

    вместо:
        try:
        ...
        except (CafeOverlapError, CafeNotFoundError, ...) as error:
        # нужно перечислять все
    """


class CafeDuplicateError(CafeError):
    """Кафе с таким названием и адресом уже существует."""

    def __init__(
        self,
        detail: str = MESSAGE_DUPLICATE_NAME_AND_ADDRESS,
    ) -> None:
        """Инициализация ошибки дублирования кафе."""
        self.detail = detail
        super().__init__(detail)


class CafeNotFoundError(CafeError):
    """Кафе не найдено."""

    def __init__(self, cafe_id: str) -> None:
        """Инициализация ошибки отсутствия кафе."""
        self.cafe_id = cafe_id
        super().__init__(f'Кафе с id {cafe_id} не найдено')


class EmptyManagersListError(CafeError):
    """Список менеджеров пуст."""

    def __init__(self, detail: str = MESSAGE_MANAGERS_ID_IS_NULL) -> None:
        """Инициализация ошибки пустого списка менеджеров."""
        self.detail = detail
        super().__init__(detail)


class DuplicateManagersError(CafeError):
    """В списке менеджеров есть дубликаты."""

    def __init__(self, detail: str = MESSAGE_MANAGERS_ID_DUPLICATE) -> None:
        """Инициализация ошибки дублирования менеджеров."""
        self.detail = detail
        super().__init__(detail)


class ManagerNotFoundError(CafeError):
    """Менеджер с таким ID не найден."""

    def __init__(self, manager_id: str) -> None:
        """Инициализация ошибки отсутствия менеджера."""
        self.manager_id = manager_id
        super().__init__(f'Менеджер с id {manager_id} не найден')


class ManagerRoleError(CafeError):
    """Пользователь не является менеджером."""

    def __init__(self, user_id: str) -> None:
        """Инициализация ошибки неверной роли пользователя."""
        self.user_id = user_id
        super().__init__(f'Пользователь {user_id} не является менеджером')
