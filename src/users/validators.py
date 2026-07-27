from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import get_logger
from src.db.utils import get_by_id_or_404
from src.users.crud import user_crud
from src.users.errors import DuplicateInfoError
from src.users.models import User

logger = get_logger(__name__)


async def check_user_exists(user_id: UUID, session: AsyncSession) -> User:
    """Проверяет, существует ли такой пользователь."""
    return await get_by_id_or_404(
        session,
        User,
        user_id,
        detail='Пользователь не найден',
        log_msg=f'Пользователь с id {user_id} не найден',
    )


async def check_user_data_duplicate(
    username: str | None,
    email: str | None,
    phone: str | None,
    session: AsyncSession,
    tg_id: str | None = None,
    exclude_id: UUID | None = None,
) -> None:
    """Проверяет, нет ли в базе данных пользователя с переданными данными."""
    checks = [
        ('username', username, 'Имя пользователя занято.'),
        ('email', email, 'Пользователь с таким email уже зарегистрирован.'),
        (
            'phone',
            phone,
            'Пользователь с таким номером телефона уже зарегистрирован.',
        ),
        ('tg_id', tg_id, 'Пользователь с таким tg_id уже зарегистрирован.'),
    ]

    filters = {field: val for field, val, _ in checks if val is not None}
    if not filters:
        logger.debug(
            'Среди переданных данных нет информации, '
            'требующей проверки на уникальность.',
        )
        return

    user = await user_crud.get_by_any_attribute(session, filters, exclude_id)

    if user:
        errors = [
            msg
            for field, val, msg in checks
            if val is not None and getattr(user, field) == val
        ]
        logger.warning(
            'При проверки данных на уникальность найдены ошибки: %s',
            errors,
        )
        raise DuplicateInfoError(*errors)
