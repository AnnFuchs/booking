class DuplicateInfoError(ValueError):
    """Ошибка дублирования данных при создании и обновлении модели."""

    pass


class ContactInfoMissingError(ValueError):
    """Ошибка отсутствия контактных данных при обновлении модели."""

    pass


class InsufficientPrivilegesError(Exception):
    """Ошибка при попытке изменить админ-поля не от админа."""

    pass


class SelfDeactivationAttemptError(Exception):
    """Ошибка при попытке деактивировать свою учетную запись."""

    pass


class UserDataConflictError(ValueError):
    """Ошибка при попытке записи данных в базу при обновлении."""

    pass
