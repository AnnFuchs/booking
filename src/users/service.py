from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.password import get_password_hash
from src.core.constants import ADMIN_ONLY_UPDATE_FIELDS, Role
from src.core.logger import get_logger
from src.db.utils import get_or_404
from src.users.crud import user_crud
from src.users.errors import (
    ContactInfoMissingError,
    DuplicateInfoError,
    InsufficientPrivilegesError,
    SelfDeactivationAttemptError,
    UserDataConflictError,
)
from src.users.models import User
from src.users.schemas import UserCreate, UserUpdate
from src.users.validators import check_user_data_duplicate

logger = get_logger(__name__)


class UserService:
    """Реализация CRUD для User."""

    async def get_user(self, session: AsyncSession, user_id: UUID) -> User:
        """Получение пользователя."""
        user = await get_or_404(
            session,
            user_crud,
            user_id,
            detail='Пользователь не найден',
            filters={'is_active': True},
            log_msg=f'Пользователь с id {user_id} не найден.',
        )
        logger.debug('Получен пользователь %s.', user.id)
        return user

    async def get_multi_users(self, session: AsyncSession) -> list[User]:
        """Получение всех пользователей."""
        users = await user_crud.get_multi(session)
        logger.debug('Получены пользователи в количестве %d.', len(users))
        return users

    async def get_user_by_login(
        self,
        session: AsyncSession,
        login: str,
    ) -> User | None:
        """Получение пользователя по логину."""
        user = await user_crud.get_by_login(session, login)
        if user is None:
            logger.debug('Пользователь с логином %s не найден', login)
        else:
            logger.debug('Получен пользователь с логином %s', login)
        return user

    async def create(self, session: AsyncSession, data: UserCreate) -> User:
        """Создание пользователя."""
        await check_user_data_duplicate(
            username=data.username,
            email=data.email,
            phone=data.phone,
            session=session,
            tg_id=data.tg_id,
        )

        hashed_password = get_password_hash(data.password.get_secret_value())

        try:
            new_user = await user_crud.create(
                session,
                obj_in=data,
                exclude_fields={'password'},
                hashed_password=hashed_password,
            )
            logger.debug('Создан новый пользователь с id %s', new_user.id)
            return new_user
        except IntegrityError:
            await session.rollback()
            logger.warning(
                'Пользователь с переданными данными уже существует.',
            )
            raise DuplicateInfoError()

    async def update(
        self,
        session: AsyncSession,
        db_user: User,
        update_data: UserUpdate,
        request_author: User | None = None,
    ) -> User:
        """Обновление данных пользователя."""
        await check_user_data_duplicate(
            username=update_data.username,
            email=update_data.email,
            phone=update_data.phone,
            session=session,
            tg_id=update_data.tg_id,
            exclude_id=db_user.id,
        )

        update_dict = update_data.model_dump(exclude_unset=True)

        has_email = update_dict.get('email', db_user.email)
        has_phone = update_dict.get('phone', db_user.phone)
        if not has_email and not has_phone:
            logger.warning(
                'При обновлении должен сохраняться заполненным '
                'email или телефон.',
            )
            raise ContactInfoMissingError()

        extra_kwargs = {}
        if 'password' in update_dict:
            secret = update_dict.pop('password')
            extra_kwargs['hashed_password'] = get_password_hash(
                secret.get_secret_value(),
            )

        if not request_author or request_author.role != Role.ADMIN:
            forbidden = set(update_dict.keys()) & set(ADMIN_ONLY_UPDATE_FIELDS)
            if forbidden:
                logger.warning(
                    'Попытка изменить поля %s, '
                    'зарезервированные для администратора, '
                    'со стороны пользователя %s',
                    ', '.join(forbidden),
                    request_author.id,
                )
                raise InsufficientPrivilegesError()

        if (
            request_author
            and db_user.id == request_author.id
            and update_dict.get('is_active') is False
        ):
            logger.warning(
                'Пользователь %s попытался деактивировать свою учетную запись',
                request_author.id,
            )
            raise SelfDeactivationAttemptError()

        try:
            for field, value in update_dict.items():
                setattr(db_user, field, value)

            for field, value in extra_kwargs.items():
                setattr(db_user, field, value)

            await session.commit()
            await session.refresh(db_user)

            logger.debug(
                'Пользователем %s обновлены данные пользователя %s.',
                request_author.id,
                db_user.id,
            )
            return db_user
        except IntegrityError:
            await session.rollback()
            logger.warning(
                'Ошибка при обновлении данных пользователя %s.',
                db_user.id,
            )
            raise UserDataConflictError()


user_service = UserService()
