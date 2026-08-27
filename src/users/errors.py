class DuplicateInfoError(Exception):
    """Ошибка дублирования данных при создании и обновлении модели."""

    pass


class ContactInfoMissingError(Exception):
    """Ошибка отсутствия контактных данных при обновлении модели."""

    pass


class InsufficientPrivilegesError(Exception):
    """Ошибка при попытке изменить админ-поля не от админа."""

    pass


class SelfDeactivationAttemptError(Exception):
    """Ошибка при попытке деактивировать свою учетную запись."""

    pass


class UserDataConflictError(Exception):
    """Ошибка при попытке записи данных в базу при обновлении."""

    pass
