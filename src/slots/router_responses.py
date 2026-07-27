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

# Responses для GET /cafes/{cafe_id}/time_slots (список слотов)
# В документации: 200, 401, 404, 422 (НЕТ 403!)
SLOTS_LIST_RESPONSES = {
    HTTPStatus.OK.value: {
        'description': 'Успешно',
        'content': {
            'application/json': {
                'schema': {
                    'type': 'array',
                    'items': {'$ref': '#/components/schemas/TimeSlotInfo'},
                },
            },
        },
    },
    HTTPStatus.UNAUTHORIZED.value: {
        'description': 'Неавторизированный пользователь',
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

# Responses для POST /cafes/{cafe_id}/time_slots (создание слота)
# В документации: 201, 400, 401, 403, 404, 422
SLOT_CREATE_RESPONSES = {
    HTTPStatus.CREATED.value: {
        'description': 'Успешно',
        'content': {
            'application/json': {
                'schema': {'$ref': '#/components/schemas/TimeSlotInfo'},
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
    HTTPStatus.NOT_FOUND.value: {
        'description': 'Данные не найдены',
        'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
    },
    HTTPStatus.UNPROCESSABLE_ENTITY.value: {
        'description': 'Ошибка валидации данных',
        'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
    },
}

# Responses для GET /cafes/{cafe_id}/time_slots/{slot_id} (получение по ID)
# В документации: 200, 400, 401, 403, 404, 422
SLOT_GET_BY_ID_RESPONSES = {
    HTTPStatus.OK.value: {
        'description': 'Успешно',
        'content': {
            'application/json': {
                'schema': {'$ref': '#/components/schemas/TimeSlotInfo'},
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
    HTTPStatus.NOT_FOUND.value: {
        'description': 'Данные не найдены',
        'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
    },
    HTTPStatus.UNPROCESSABLE_ENTITY.value: {
        'description': 'Ошибка валидации данных',
        'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
    },
}

# Responses для PATCH /cafes/{cafe_id}/time_slots/{slot_id} (обновление слота)
# В документации: 200, 400, 401, 403, 404, 422
SLOT_UPDATE_RESPONSES = {
    HTTPStatus.OK.value: {
        'description': 'Успешно',
        'content': {
            'application/json': {
                'schema': {'$ref': '#/components/schemas/TimeSlotInfo'},
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
    HTTPStatus.NOT_FOUND.value: {
        'description': 'Данные не найдены',
        'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
    },
    HTTPStatus.UNPROCESSABLE_ENTITY.value: {
        'description': 'Ошибка валидации данных',
        'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
    },
}
