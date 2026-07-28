from pydantic import EmailStr, Field, SecretStr, field_validator
from pydantic_extra_types.phone_numbers import PhoneNumber
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.constants import BASE_DIR, MIN_LENGTH


class Settings(BaseSettings):
    """Настройки приложения."""

    app_title: str = Field(
        default='Система бронирования мест в кафе',
        min_length=MIN_LENGTH,
    )
    app_description: str = Field(default='.', min_length=MIN_LENGTH)
    app_servers: list[dict[str, str]] = [
        {
            'url': 'http://localhost:8000',
            'description': 'Локальный сервер',
        },
    ]
    cors_origin: str = 'http://localhost:8000'

    postgres_user: str = Field(min_length=MIN_LENGTH)
    postgres_password: SecretStr
    postgres_db: str = Field(min_length=MIN_LENGTH)
    postgres_server: str = Field(min_length=MIN_LENGTH)
    postgres_port: int
    redis_host: str = 'redis'
    redis_port: int = 6379
    redis_db: int = 0
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    secret_key: SecretStr
    algorithm: str = Field(min_length=MIN_LENGTH)

    first_superuser_login: EmailStr | PhoneNumber
    first_superuser_password: SecretStr

    mail_username: str
    mail_password: SecretStr
    mail_from: str
    mail_server: str
    mail_port: int = 2525
    mail_starttls: bool = False
    mail_ssl_tls: bool = False
    mail_from_name: str = 'cafe booking'

    _env_file = BASE_DIR / 'infra' / '.env'

    model_config = SettingsConfigDict(
        env_file=_env_file if _env_file.exists() else None,
        env_file_encoding='utf-8',
        case_sensitive=False,
    )

    @field_validator('postgres_port')
    @classmethod
    def check_port(cls, value: int) -> int:
        """Проверка номера порта."""
        if not 1 <= value <= 65535:
            raise ValueError('Номер порта должен быть в диапазоне 1-65535')
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        """Создание списка разрешенных источников для CORS."""
        return [origin.strip() for origin in self.cors_origin.split(',')]

    @property
    def database_url(self) -> str:
        """Создание URL базы данных."""
        return (
            f'postgresql+asyncpg://{self.postgres_user}:'
            f'{self.postgres_password.get_secret_value()}'
            f'@{self.postgres_server}:'
            f'{self.postgres_port}/{self.postgres_db}'
        )

    @property
    def sync_database_url(self) -> str:
        """Создание синхронного URL базы данных для Celery."""
        return (
            f'postgresql+psycopg2://{self.postgres_user}:'
            f'{self.postgres_password.get_secret_value()}'
            f'@{self.postgres_server}:'
            f'{self.postgres_port}/{self.postgres_db}'
        )

    @property
    def redis_url(self) -> str:
        """Создание URL Redis."""
        return f'redis://{self.redis_host}:{self.redis_port}/{self.redis_db}'

    @property
    def effective_celery_broker_url(self) -> str:
        """Получение URL брокера Celery."""
        return self.celery_broker_url or self.redis_url

    @property
    def effective_celery_result_backend(self) -> str:
        """Получение backend Celery."""
        return self.celery_result_backend or self.redis_url

    @property
    def jwt_auth_data(self) -> dict:
        """Получаение данных для генерации jwt токена."""
        return {
            'secret_key': self.secret_key.get_secret_value(),
            'algorithm': self.algorithm,
        }


settings = Settings()
