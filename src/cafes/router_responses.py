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
    HTTPStatus.UNAUTHORIZED.value: {
        'description': 'Неавторизированный пользователь',
        'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
    },
    HTTPStatus.UNPROCESSABLE_ENTITY.value: {
        'description': 'Ошибка валидации данных',
        'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
    },
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
    HTTPStatus.BAD_REQUEST.value: {
        'description': 'Ошибка в параметрах запроса',
        'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
    },
    HTTPStatus.UNAUTHORIZED.value: {
        'description': 'Неавторизированный пользователь',
        'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
    },
    HTTPStatus.FORBIDDEN.value: {
        'description': 'Доступ запрещен',
        'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
    },
    HTTPStatus.CONFLICT.value: {
        'description': 'Кафе с таким названием и адресом уже существует',
        'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
    },
    HTTPStatus.UNPROCESSABLE_ENTITY.value: {
        'description': 'Ошибка валидации данных',
        'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
    },
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
    HTTPStatus.BAD_REQUEST.value: {  # ← ДОБАВИТЬ
        'description': 'Ошибка в параметрах запроса',
        'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
    },
    HTTPStatus.UNAUTHORIZED.value: {
        'description': 'Неавторизированный пользователь',
        'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
    },
    HTTPStatus.FORBIDDEN.value: {
        'description': 'Доступ запрещен',
        'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
    },
    HTTPStatus.NOT_FOUND.value: {
        'description': 'Данные не найдены',
        'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
    },
    HTTPStatus.UNPROCESSABLE_ENTITY.value: {
        'description': 'Ошибка валидации данных',
        'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
    },
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
    HTTPStatus.BAD_REQUEST.value: {  # ← ДОБАВИТЬ
        'description': 'Ошибка в параметрах запроса',
        'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
    },
    HTTPStatus.UNAUTHORIZED.value: {
        'description': 'Неавторизированный пользователь',
        'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
    },
    HTTPStatus.FORBIDDEN.value: {
        'description': 'Доступ запрещен',
        'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
    },
    HTTPStatus.NOT_FOUND.value: {
        'description': 'Данные не найдены',
        'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
    },
    HTTPStatus.CONFLICT.value: {
        'description': 'Кафе с таким названием и адресом уже существует',
        'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
    },
    HTTPStatus.UNPROCESSABLE_ENTITY.value: {
        'description': 'Ошибка валидации данных',
        'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
    },
}
