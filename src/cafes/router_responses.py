from http import HTTPStatus

CUSTOM_ERROR_SCHEMA = {
    'type': 'object',
    'properties': {
        'code': {'type': 'integer', 'title': 'Code'},
        'message': {'type': 'string', 'title': 'Message'},
    },
    'required': ['code', 'message'],
    'title': 'CustomError',
}


def _error(status: int, description: str) -> dict:
    """Возвращает словарь с кодом ответа и стандартной структурой ошибки."""
    return {
        status: {
            'description': description,
            'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
        },
    }


# Общие ошибочные ответы
UNAUTHORIZED = _error(
    HTTPStatus.UNAUTHORIZED,
    'Неавторизированный пользователь',
)
FORBIDDEN = _error(HTTPStatus.FORBIDDEN, 'Доступ запрещен')
NOT_FOUND = _error(HTTPStatus.NOT_FOUND, 'Данные не найдены')
CONFLICT = _error(
    HTTPStatus.CONFLICT,
    'Кафе с таким названием и адресом уже существует',
)
UNPROCESSABLE = _error(
    HTTPStatus.UNPROCESSABLE_ENTITY,
    'Ошибка валидации данных',
)
BAD_REQUEST = _error(HTTPStatus.BAD_REQUEST, 'Ошибка в параметрах запроса')

# Responses для GET /cafes (список кафе)
CAFES_LIST_RESPONSES = {
    HTTPStatus.OK.value: {
        'description': 'Успешно',
        'content': {
            'application/json': {
                'schema': {
                    'type': 'array',
                    'items': {'$ref': '#/components/schemas/CafeInfo'},
                },
            },
        },
    },
    **UNAUTHORIZED,
    **UNPROCESSABLE,
}

# Responses для POST /cafes (создание кафе)
CAFE_CREATE_RESPONSES = {
    HTTPStatus.CREATED.value: {
        'description': 'Успешно',
        'content': {
            'application/json': {
                'schema': {'$ref': '#/components/schemas/CafeInfo'},
            },
        },
    },
    **BAD_REQUEST,
    **UNAUTHORIZED,
    **FORBIDDEN,
    **CONFLICT,
    **UNPROCESSABLE,
}

# Responses для GET /cafes/{cafe_id} (получение по ID)
CAFE_GET_BY_ID_RESPONSES = {
    HTTPStatus.OK.value: {
        'description': 'Успешно',
        'content': {
            'application/json': {
                'schema': {'$ref': '#/components/schemas/CafeInfo'},
            },
        },
    },
    **BAD_REQUEST,
    **UNAUTHORIZED,
    **FORBIDDEN,
    **NOT_FOUND,
    **UNPROCESSABLE,
}

# Responses для PATCH /cafes/{cafe_id} (обновление кафе)
CAFE_UPDATE_RESPONSES = {
    HTTPStatus.OK.value: {
        'description': 'Успешно',
        'content': {
            'application/json': {
                'schema': {'$ref': '#/components/schemas/CafeInfo'},
            },
        },
    },
    **BAD_REQUEST,
    **UNAUTHORIZED,
    **FORBIDDEN,
    **NOT_FOUND,
    **CONFLICT,
    **UNPROCESSABLE,
}
