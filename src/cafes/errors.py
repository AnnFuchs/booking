class CafeDuplicateError(Exception):
    """Ошибка при дублировании названия или адреса кафе с имеющимся базе."""

    pass


class CafeNotFoundError(Exception):
    """Ошибка при отсутствии кафе в базе."""

    pass


class EmptyManagersListError(Exception):
    """Ошибка при передаче пустого списка менеджеров."""

    pass


class ManagerNotFoundError(Exception):
    """Ошибка при отсутствии менеджера с переданным ID в базе."""

    pass


class ManagerRoleError(Exception):
    """Ошибка при несоотстветствии роли пользователя менеджерской."""

    pass


class ManagerListIncorrectError(Exception):
    """Ошибка при невалидных значениях в листе менеджеров."""

    pass


class CafeManagerAlreadyBusyError(Exception):
    """Менеджер уже привязан к другому кафе."""

    pass
