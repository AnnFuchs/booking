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

_ERROR_RESPONSES = {
    'bad_request': {
        HTTPStatus.BAD_REQUEST.value: {
            'description': 'Ошибка в параметрах запроса',
            'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
        },
    },
    'unauthorized': {
        HTTPStatus.UNAUTHORIZED.value: {
            'description': 'Неавторизированный пользователь',
            'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
        },
    },
    'forbidden': {
        HTTPStatus.FORBIDDEN.value: {
            'description': 'Доступ запрещен',
            'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
        },
    },
    'not_found': {
        HTTPStatus.NOT_FOUND.value: {
            'description': 'Данные не найдены',
            'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
        },
    },
    'unprocessable': {
        HTTPStatus.UNPROCESSABLE_ENTITY.value: {
            'description': 'Ошибка валидации данных',
            'content': {'application/json': {'schema': CUSTOM_ERROR_SCHEMA}},
        },
    },
}


def _combine_errors(*error_keys: str) -> dict:
    """Комбинирует несколько ошибок в один словарь."""
    result = {}
    for key in error_keys:
        result.update(_ERROR_RESPONSES[key])
    return result


USERS_LIST_RESPONSES = _combine_errors('unauthorized', 'forbidden')

USERS_CREATE_RESPONSES = _combine_errors('bad_request', 'unprocessable')

USER_GET_BY_ID_RESPONSES = _combine_errors(
    'unauthorized',
    'forbidden',
    'not_found',
    'unprocessable',
)

USER_UPDATE_BY_ID_RESPONSES = _combine_errors(
    'bad_request',
    'unauthorized',
    'forbidden',
    'not_found',
    'unprocessable',
)

USER_GET_ME_RESPONSES = _combine_errors('forbidden')

USER_UPDATE_ME_RESPONSES = _combine_errors(
    'bad_request',
    'forbidden',
    'unprocessable',
)
