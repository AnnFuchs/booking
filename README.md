# Система бронирования мест в кафе

## Описание проекта:

Проект представляет собой **API для системы бронирования мест в кафе**. Позволяет управлять кафе, столами, временными слотами и бронированиями. Реализована ролевая модель (администратор, менеджер, пользователь) с разграничением прав доступа к эндпоинтам.

**Репозиторий:** https://github.com/Yandex-Practicum-Students/64_65_booking_seats_team_3

## Основные возможности:

### Управление пользователями
- Регистрация и аутентификация (JWT токены)
- Просмотр и обновление профиля пользователя
- Ролевая модель: администратор, менеджер, пользователь
- Только администраторы и менеджеры могут работать со всеми пользователями
- Автоматическое создание первого администратора при старте приложения

### Управление кафе
- Создание, просмотр, обновление кафе (администраторы и менеджеры)
- Назначение менеджеров для управления кафе
- Фильтрация кафе по активности
- Для обычных пользователей доступны только активные кафе

### Управление столами
- Создание столов в конкретном кафе
- Указание количества посадочных мест и описания
- Просмотр всех столов в кафе с фильтрацией по активности

### Управление временными слотами
- Создание временных интервалов для бронирования (начало и конец)
- Валидация: время начала должно быть меньше времени окончания
- Запрет на пересекающиеся слоты в одном кафе

### Управление бронированиями
- Бронирование стола на определенную дату и время
- Связь бронирования с кафе, столом и временным слотом
- Просмотр истории бронирований (пользователь видит только свои)
- Статусы бронирований: BOOKING, CANCELED, ACTIVE, COMPLETED

### Уведомления
- Email-оповещения о статусе бронирования через SMTP
- Асинхронная отправка уведомлений с помощью **Celery**
- Мониторинг задач через **Flower** (доступен на порту 5555)
- Настройка SMTP-сервера через переменные окружения

### Медиа-файлы
- Загрузка и хранение изображений (jpg, png, до 5 МБ)
- Поддержка UUID для идентификации файлов
- Только администраторы и менеджеры могут загружать изображения
- Файлы сохраняются в Docker-том `media` и отдаются через Nginx

## Стек технологий:

| Технология | Назначение |
|------------|------------|
| Python 3.12 | Основной язык разработки |
| FastAPI | Веб-фреймворк |
| SQLAlchemy 2.0 | ORM (асинхронный) |
| Pydantic v2 | Валидация данных и схемы |
| Alembic | Миграции базы данных |
| PostgreSQL 17 | Основная база данных |
| AsyncPG | Асинхронный драйвер PostgreSQL |
| Redis 8 | Брокер сообщений для Celery |
| Celery 5.6 | Асинхронная обработка задач |
| Flower 2.0 | Мониторинг Celery задач |
| Nginx | Reverse-proxy и раздача статики |
| Docker / Docker Compose | Контейнеризация |
| python-jose | JWT токены |
| python-multipart | Загрузка файлов |
| Ruff | Линтер и форматтер кода |
| Pre-commit | Автоматическая проверка кода |

## Роли и права доступа:

| Роль | Права |
|------|-------|
| **Администратор (ADMIN)** | Полный доступ ко всем ресурсам |
| **Менеджер (MANAGER)** | Управление своим кафе, столами, бронированиями |
| **Пользователь (USER)** | Просмотр активных кафе, создание бронирований |

## API документация

Интерактивная документация API доступна в формате Swagger UI:

- **Local development:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Production:** `https://your-domain.com/api/v1/docs`

Альтернативный формат документации (ReDoc):

- **Local:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Production:** `https://your-domain.com/api/v1/redoc`

> **Примечание:** Swagger UI позволяет выполнять интерактивные запросы к API, включая авторизацию с использованием JWT-токенов. Для тестирования защищённых эндпоинтов необходимо предварительно получить токен через эндпоинт `/api/v1/auth/login` и авторизоваться в интерфейсе Swagger, нажав кнопку **Authorize**.

## Установка и запуск:

### Способ 1: Локальный запуск через Docker Compose (рекомендуемый)

Этот способ позволяет запустить все необходимые сервисы без установки PostgreSQL и Redis локально.

#### 1. Подготовка окружения

```bash
git clone https://github.com/Yandex-Practicum-Students/64_65_booking_seats_team_3.git
cd 64_65_booking_seats_team_3
```

#### 2. Создать файл `.env` в директории `infra/`

Используйте пример из `infra/.env.example` с параметрами для локальной разработки:

```bash
# PostgreSQL
POSTGRES_USER=booking_user
POSTGRES_PASSWORD=dev_password
POSTGRES_DB=cafe_booking
POSTGRES_SERVER=db
POSTGRES_PORT=5432

# API
APP_TITLE=Система бронирования мест в кафе (DEV)
SECRET_KEY=dev_secret_key_min_32_characters_long
ALGORITHM=HS256

# Первый суперпользователь
FIRST_SUPERUSER_LOGIN=admin@example.com
FIRST_SUPERUSER_PASSWORD=admin

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
```

#### 3. Запустить контейнеры

```bash
cd infra
docker-compose up -d --build
```

**Что произойдет:**

- `db` — PostgreSQL 17 с оптимизированными настройками
- `redis` — Redis 8 для Celery
- `api` — FastAPI приложение с hot-reload (изменения в коде применяются автоматически)
- `celery_worker` — Celery worker для фоновых задач
- `flower` — Мониторинг Celery на [http://localhost:5555](http://localhost:5555)

#### 4. Проверка работы

```bash
# Статус контейнеров
docker-compose ps

# Логи API
docker-compose logs -f api

# Swagger UI
http://localhost:8000/docs
```

#### 5. Остановка контейнеров

```bash
docker-compose down

# Или с удалением volumes (БД будет очищена)
docker-compose down -v
```

---

### Способ 2: Развертывание на production сервере

Этот способ предназначен для развертывания приложения на удаленном сервере с использованием Docker Compose, Nginx и SSL-сертификатов.

#### Требования к серверу

- **ОС:** Linux (Ubuntu 20.04+, Debian 11+, или аналог)
- **Docker:** версия 20.10+
- **Docker Compose:** версия 2.0+
- **Открытые порты:** 80 (HTTP), 443 (HTTPS)
- **Доменное имя:** с настроенными DNS-записями, указывающими на IP сервера

#### 1. Подключение к серверу и клонирование репозитория

```bash
# Подключиться к серверу по SSH
ssh user@your-server.com

# Клонировать репозиторий
git clone https://github.com/Yandex-Practicum-Students/64_65_booking_seats_team_3.git
cd 64_65_booking_seats_team_3
```

#### 2. Настройка переменных окружения

Создайте файл `infra/.env` с production-настройками:

```bash
# PostgreSQL
POSTGRES_USER=booking_user
POSTGRES_PASSWORD=your_strong_password_here
POSTGRES_DB=cafe_booking
POSTGRES_SERVER=db
POSTGRES_PORT=5432

# API
APP_TITLE=Система бронирования мест в кафе
APP_DESCRIPTION=API для бронирования столов в кафе
SECRET_KEY=your_super_secret_key_min_32_chars_random_string
ALGORITHM=HS256

# Первый администратор
FIRST_SUPERUSER_LOGIN=admin@yourdomain.com
FIRST_SUPERUSER_PASSWORD=secure_admin_password

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Email (настройте реальные данные)
MAIL_USERNAME=noreply@yourdomain.com
MAIL_PASSWORD=your_smtp_password
MAIL_FROM=noreply@yourdomain.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_STARTTLS=true
MAIL_SSL_TLS=false
MAIL_FROM_NAME=Cafe Booking
```

> **⚠️ Важно:** Используйте надежные пароли и храните файл `.env` в безопасности. Не коммитьте его в Git.

#### 3. Настройка SSL-сертификатов (HTTPS)

**Вариант A: Let's Encrypt (рекомендуется)**

```bash
# Установить certbot
sudo apt update
sudo apt install certbot

# Получить сертификат для вашего домена
sudo certbot certonly --standalone -d your-domain.com

# Сертификаты будут размещены в:
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem
```

**Вариант B: Без HTTPS (только для тестирования)**

Если SSL не требуется, отредактируйте `infra/nginx.conf`:
- Закомментируйте блок `server` для порта 443
- Оставьте только блок для порта 80

#### 4. Настройка Nginx конфигурации

Отредактируйте `infra/nginx.conf`, заменив `team3.ddns.net` на ваш домен:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;  # Ваш домен

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # ... остальная конфигурация
}
```

#### 5. Запуск приложения

```bash
cd infra
docker-compose -f docker-compose.production.yml up -d --build
```

**Развернутые сервисы:**

| Сервис | Описание | Доступ |
|--------|----------|--------|
| `nginx` | Reverse-proxy с SSL | Порты 80, 443 |
| `api` | FastAPI приложение | Внутренний порт 8000 |
| `db` | PostgreSQL 17 | Внутренний порт 5432 |
| `redis` | Redis 8 (брокер Celery) | Внутренний порт 6379 |
| `celery_worker` | Обработчик фоновых задач | — |
| `flower` | Мониторинг Celery | Порт 5555 |

#### 6. Проверка развертывания

```bash
# Проверить статус контейнеров
docker-compose -f docker-compose.production.yml ps

# Проверить логи
docker-compose -f docker-compose.production.yml logs -f api

# Проверить доступность API
curl https://your-domain.com/api/v1/docs

# Проверить health endpoint
curl https://your-domain.com/api/v1/health
```

#### 7. Автоматическое обновление SSL-сертификатов

```bash
# Настроить cron для автоматического обновления
sudo crontab -e

# Добавить строку (обновление каждый понедельник в 3:00)
0 3 * * 1 certbot renew --quiet && docker-compose -f /path/to/infra/docker-compose.production.yml restart nginx
```

#### 8. Обновление приложения

```bash
# Остановить контейнеры
cd infra
docker-compose -f docker-compose.production.yml down

# Получить последние изменения
cd ..
git pull origin main

# Пересобрать и запустить
cd infra
docker-compose -f docker-compose.production.yml up -d --build

# Проверить миграции (применяются автоматически при старте)
docker-compose -f docker-compose.production.yml logs api | grep "alembic"
```

---

### Способ 3: Локальный запуск без Docker (для продвинутых пользователей)

<details>
<summary>Развернуть инструкцию</summary>

Если вы предпочитаете работать без Docker, вам понадобится локально установить:
- **Python 3.12**
- **PostgreSQL 17**
- **Redis 8**

#### Быстрая настройка

```bash
# 1. Клонировать и создать venv
git clone https://github.com/Yandex-Practicum-Students/64_65_booking_seats_team_3.git
cd 64_65_booking_seats_team_3
python3.12 -m venv venv
source venv/bin/activate  # Linux/MacOS
# venv\Scripts\activate  # Windows

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Настроить .env в infra/.env
# Используйте POSTGRES_SERVER=localhost и REDIS_HOST=localhost

# 4. Создать БД PostgreSQL
psql -U postgres
CREATE DATABASE cafe_booking;
CREATE USER booking_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE cafe_booking TO booking_user;
\q

# 5. Применить миграции
alembic -c src/alembic.ini upgrade head

# 6. Запустить Redis
redis-server
# или: docker run -d -p 6379:6379 redis:8-alpine

# 7. Запустить Celery worker (в отдельном терминале)
celery -A src.celery_app.app.celery_app worker --loglevel=info

# 8. Запустить API
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

</details>

---

## Примеры запросов

### Регистрация пользователя

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure_password"
  }'
```

### Получение токена

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login": "john@example.com", "password": "secure_password"}'
```

### Создание кафе (только для администраторов и менеджеров)

```bash
curl -X POST http://localhost:8000/api/v1/cafes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Уютное кафе",
    "address": "ул. Центральная, 123",
    "phone": "+79123456789",
    "description": "Уютное место для встреч"
  }'
```

### Создание бронирования

```bash
curl -X POST http://localhost:8000/api/v1/bookings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "cafe_id": "cafe-uuid-here",
    "booking_date": "2024-12-25",
    "guest_number": 4,
    "note": "Особое место у окна"
  }'
```

### Получение списка кафе

```bash
curl -X GET http://localhost:8000/api/v1/cafes \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Структура директорий (важно для Docker)

Проект предполагает следующую структуру:

```text
project_root/              # Корень проекта
├── infra/                 # Инфраструктурные файлы
│   ├── .env               # Переменные окружения
│   ├── docker-compose.production.yml
│   ├── celery.Dockerfile
│   ├── nginx.conf
│   └── entrypoint.sh
├── src/                   # Исходный код
│   ├── main.py
│   ├── alembic/
│   ├── alembic.ini
│   └── ...
└── Dockerfile             # Dockerfile для API
```

> **Важно:** в файле `docker-compose.production.yml` указан параметр `context: ..`, что означает сборку контекста из корня проекта. Файл `.env` должен находиться в директории `infra/`, так как именно оттуда он загружается настройками приложения.

---

## Управление миграциями

Миграции накатываются автоматически через `entrypoint.sh` при старте API-контейнера.

### Ручное управление миграциями

```bash
# Войти в контейнер api
docker exec -it cafe_booking-api-1 bash

# Создать новую миграцию
alembic -c src/alembic.ini revision --autogenerate -m "description"

# Применить миграции
alembic -c src/alembic.ini upgrade head

# Откатить миграцию
alembic -c src/alembic.ini downgrade -1
```

---

## Мониторинг и логи

### Доступ к мониторингу

| Сервис | Локальная разработка | Production |
|--------|---------------------|------------|
| **Flower** (Celery) | `http://localhost:5555` | `http://your-domain.com:5555` |
| **Swagger UI** | `http://localhost:8000/docs` | `https://your-domain.com/api/v1/docs` |

### Просмотр логов

```bash
# Логи всех сервисов
docker-compose -f infra/docker-compose.production.yml logs -f

# Логи конкретного сервиса
docker-compose -f infra/docker-compose.production.yml logs -f api
docker-compose -f infra/docker-compose.production.yml logs -f celery_worker
docker-compose -f infra/docker-compose.production.yml logs -f nginx

# Последние 100 строк логов API
docker-compose -f infra/docker-compose.production.yml logs --tail=100 api
```

---

## Резервное копирование

### Бэкап базы данных

```bash
docker exec cafe_booking-db-1 pg_dump -U booking_user cafe_booking > backup_$(date +%Y%m%d).sql
```

### Бэкап медиа-файлов

```bash
docker run --rm -v cafe_booking_media:/media -v $(pwd):/backup alpine tar czf /backup/media_backup_$(date +%Y%m%d).tar.gz -C /media .
```

---

## Тестирование

Проект покрыт тестами с использованием `pytest` и `pytest-asyncio`.

### Покрытие тестами

В проекте реализовано **частичное покрытие тестами** критических модулей:

| Модуль | Покрытие | Количество тестов | Описание |
|--------|----------|-------------------|----------|
| **Bookings API** | ✅ Высокое | 18 тестов | Создание, обновление, отмена бронирований, проверка лимитов, конфликтов, валидация |
| **Media API** | ✅ Высокое | 8 тестов | Загрузка изображений, проверка размеров, форматов, прав доступа |
| **Auth** | ⚠️ Частичное | Фикстуры | JWT токены, роли (используется в других тестах) |
| **Cafes, Tables, Slots, Users** | ❌ Нет | 0 тестов | Требуется добавить тесты CRUD операций |

**Итого:** 26+ тестов покрывают основные бизнес-сценарии бронирований и работы с медиа.

### Структура тестов

```text
tests/
├── conftest.py              # Основные фикстуры (event loop, async_client, manage_db)
├── fixtures/                # Модульные фикстуры
│   ├── auth.py             # test_user, test_admin, user_headers, admin_headers
│   ├── db.py               # session, create_user (фабрика пользователей)
│   └── entities.py         # test_cafe, test_table, test_slot, test_table_slot
├── test_booking_api.py     # 18 тестов API бронирований
└── test_media_api.py       # 8 тестов API медиа-файлов
```

### Ключевые тестовые сценарии

**Бронирования:**
- ✅ Создание и получение бронирования
- ✅ Обновление полей и смена статуса
- ✅ Мягкое удаление (soft delete)
- ✅ Проверка лимита 3 активных бронирований
- ✅ Конфликт бронирования одного слота
- ✅ Запрет бронирования на прошедшую дату
- ✅ Валидация полей (длина комментария, пустые столы)
- ✅ Разграничение прав (менеджер не может отменить чужую бронь)

**Медиа:**
- ✅ Загрузка изображений (PNG → JPEG конвертация)
- ✅ Проверка прав доступа (admin/manager)
- ✅ Валидация формата и размера файла (макс. 5 МБ)
- ✅ Получение изображения по media_id

### Запуск тестов

```bash
# Локальный запуск всех тестов
pytest -v

# Запуск конкретного файла
pytest tests/test_booking_api.py -v

# Запуск с покрытием кода
pytest --cov=src --cov-report=html

# Запуск тестов в Docker
docker exec cafe_booking-api-1 pytest -v
```

### Конфигурация pytest

Настройки находятся в `pytest.ini` и включают:
- Асинхронные тесты через `pytest-asyncio` (scope='session')
- Автоматический поиск тестов в директории `tests/`
- Плагины фикстур через `pytest_plugins`
- Настройки вывода и маркеров

---

## Структура исходного кода

```text
src/
├── auth/                    # Аутентификация и JWT токены
│   ├── dependencies.py      # Dependency injection для авторизации
│   ├── jwt.py              # Работа с JWT токенами
│   ├── password.py         # Хеширование паролей
│   ├── router.py           # Эндпоинты аутентификации
│   ├── schemas.py          # Pydantic схемы
│   └── service.py          # Бизнес-логика
├── cafes/                  # Управление кафе
├── tables/                 # Управление столами
├── slots/                  # Управление временными слотами
├── bookings/               # Управление бронированиями
│   ├── dependencies.py     # Зависимости для бронирований
│   ├── notifications.py    # Уведомления о бронированиях
│   └── utils.py           # Вспомогательные функции
├── users/                  # Управление пользователями
├── media/                  # Работа с изображениями
├── notifications/          # Система уведомлений
│   ├── config.py          # Настройки email
│   └── email.py           # Отправка email
├── celery_app/            # Конфигурация Celery и задачи
│   ├── app.py             # Инициализация Celery
│   └── tasks/             # Фоновые задачи
│       └── booking_notif_tasks.py
├── crud/                   # Базовые CRUD операции
│   ├── crud.py            # Базовый класс CRUD
│   └── utils.py           # Утилиты для CRUD
├── core/                   # Конфигурация и утилиты
│   ├── config.py          # Настройки приложения (Pydantic Settings)
│   ├── constants.py       # Константы проекта
│   ├── logger.py          # Настройка логирования
│   ├── middleware.py      # Middleware (User Context, CORS)
│   └── router.py          # Главный роутер
├── db/                     # Настройка БД
│   ├── base.py            # Базовая модель SQLAlchemy
│   ├── first_admin.py     # Создание первого администратора
│   ├── models_for_alembic.py  # Импорт моделей для миграций
│   ├── session.py         # Асинхронная сессия БД
│   └── utils.py           # Утилиты для работы с БД
├── alembic/                # Миграции базы данных
│   ├── env.py             # Конфигурация Alembic
│   └── versions/          # История миграций
├── alembic.ini            # Настройки Alembic
└── main.py                # Точка входа (FastAPI app)
```

---

## Инструменты разработки

Проект использует современные инструменты для поддержания качества кода:

### Ruff — линтер и форматтер

Настройки находятся в `ruff.toml`. Ruff проверяет стиль кода, находит потенциальные ошибки и автоматически форматирует код.

```bash
# Проверка кода
ruff check .

# Автоматическое исправление
ruff check --fix .

# Форматирование кода
ruff format .
```

### Pre-commit hooks

Автоматическая проверка кода перед каждым коммитом. Настройки в `.pre-commit-config.yaml`.

```bash
# Установка хуков
pre-commit install

# Ручной запуск проверки
pre-commit run --all-files
```

### GitHub Actions CI/CD

Проект использует GitHub Actions для автоматизации:

- **style_check.yml** — проверка стиля кода с помощью Ruff
- **main.yml** — основной CI/CD пайплайн

Пайплайны запускаются автоматически при push и pull request.

---

## Устранение неполадок

### API не стартует из-за ошибок миграций

```bash
# Проверить доступность базы данных
docker exec cafe_booking-api-1 python -c "import asyncio; from src.db.session import test_connection; asyncio.run(test_connection())"

# Вручную применить миграции
docker exec cafe_booking-api-1 alembic -c src/alembic.ini upgrade head
```

### Celery задачи не выполняются

```bash
# Проверить статус Celery воркера
docker exec cafe_booking-celery_worker-1 celery -A src.celery_app.app.celery_app status

# Проверить соединение с Redis
docker exec cafe_booking-redis-1 redis-cli ping
```

### Ошибка загрузки переменных окружения

Убедитесь, что файл `.env` находится в директории `infra/`, а не в корне проекта. Настройки приложения ожидают файл именно по пути `infra/.env`.

### Проблемы с hot-reload в Docker

Если изменения в коде не применяются автоматически при использовании `docker-compose.yml`:

```bash
# Пересоздать контейнер API
docker-compose restart api

# Или пересобрать образ
docker-compose up -d --build api
```

### CORS ошибки

Проверьте настройки CORS в `.env` или `src/core/config.py`. По умолчанию разрешены методы: `GET`, `POST`, `PATCH`.

### Ошибки валидации Pydantic

Проект использует **Pydantic v2**. При обновлении схем убедитесь в совместимости с новым API Pydantic.

---

## Авторы

**Тимлид проекта:**

- **Павел Седых** — [GitHub](https://github.com/Pavel7175)

**Команда разработки:**

- **Анна Фукс** — [GitHub](https://github.com/AnnFuchs)
- **Денис Поляков** — [GitHub](https://github.com/desoutme)
- **Кирилл Феклисов** — [GitHub](https://github.com/philya8)
- **Надежда Костанцо** — [GitHub](https://github.com/Nadi-Costanzo)
- **Дмитрий Силачев** — [GitHub](https://github.com/dsilachev)
