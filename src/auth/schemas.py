from pydantic import BaseModel, ConfigDict, SecretStr

from src.core.constants import MAX_LEN, MIN_LEN, TOKEN_TYPE


class AuthData(BaseModel):
    """Схема аутентификации."""

    login: str
    password: SecretStr

    model_config = ConfigDict(
        extra='forbid',
        str_strip_whitespace=True,
        str_min_length=MIN_LEN,
        str_max_length=MAX_LEN,
    )


class AuthToken(BaseModel):
    """Схема получения токена."""

    access_token: str
    token_type: str = TOKEN_TYPE

    model_config = ConfigDict(extra='forbid')
