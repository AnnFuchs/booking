from pydantic import BaseModel, ConfigDict, SecretStr

from src.core.constants import TOKEN_TYPE


class AuthData(BaseModel):
    """Схема аутентификации."""

    login: str
    password: SecretStr

    model_config = ConfigDict(extra='forbid')


class AuthToken(BaseModel):
    """Схема получения токена."""

    access_token: str
    token_type: str = TOKEN_TYPE

    model_config = ConfigDict(extra='forbid')
