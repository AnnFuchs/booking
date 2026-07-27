# Система бронирования мест в кафе

## Описание проекта:

Проект представляет собой **API для системы бронирования мест в кафе**. Позволяет управлять кафе, столами, временными слотами, бронированиями, пользователями, блюдами и акциями. Реализована ролевая модель (администратор, менеджер, пользователь) с разграничением прав доступа к эндпоинтам.

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

### Асинхронные задачи (Celery)
- **Обработка уведомлений** (email-оповещения о статусе бронирования)
- **Периодические задачи** (например, очистка неактивных бронирований)
- Мониторинг задач через **Flower** (доступен на порту 5555)

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
| Redis 8 | Брокер сообщений для Celery |
| Celery 5.6 | Асинхронная обработка задач |
| Flower 2.0 | Мониторинг Celery задач |
| Nginx | Reverse-proxy и раздача статики |
| Docker / Docker Compose | Контейнеризация |
| python-jose | JWT токены |
| python-multipart | Загрузка файлов |

## Роли и права доступа:

| Роль | Права |
|------|-------|
| **Администратор (ADMIN)** | Полный доступ ко всем ресурсам |
| **Менеджер (MANAGER)** | Управление своим кафе, столами, бронированиями |
| **Пользователь (USER)** | Просмотр активных кафе, создание бронирований |

## API документация

Интерактивная документация API доступна в формате Swagger UI по следующим адресам:

- **Production environment:** [https://team3.ddns.net/api/v1/docs](https://team3.ddns.net/api/v1/docs)
- **Local development:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Альтернативный формат документации (ReDoc):

- **Local:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

> **Примечание:** Production-экземпляр API развернут с поддержкой HTTPS. Swagger UI позволяет выполнять интерактивные запросы к API, включая авторизацию с использованием JWT-токенов. Для тестирования защищённых эндпоинтов необходимо предварительно получить токен через эндпоинт `/api/v1/auth/login` и авторизоваться в интерфейсе Swagger, нажав кнопку **Authorize**.

## Установка и запуск:

### Способ 1: Локальный запуск (для разработки)

#### 1. Клонировать репозиторий

```bash
git clone https://github.com/Yandex-Practicum-Students/64_65_booking_seats_team_3.git
cd 64_65_booking_seats_team_3
```

#### 2. Создать и активировать виртуальное окружение

**Windows:**
```bash
py -3.12 -m venv venv
venv\Scripts\activate
```

**Linux/MacOS:**
```bash
python3.12 -m venv venv
source venv/bin/activate
```

#### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

#### 4. Создать файл `.env` в директории `infra/`

Переменные окружения загружаются из файла `infra/.env`. Пример содержимого:

```bash
# PostgreSQL
POSTGRES_USER=booking_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=cafe_booking
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432

# API
APP_TITLE=Система бронирования мест в кафе
APP_DESCRIPTION=API для бронирования столов в кафе
SECRET_KEY=your_secret_key_here_min_32_chars
ALGORITHM=HS256

# Первый суперпользователь
FIRST_SUPERUSER_LOGIN=admin@example.com
FIRST_SUPERUSER_PASSWORD=admin_password

# Redis для Celery
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Email для уведомлений (опционально)
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_FROM=noreply@yourdomain.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_STARTTLS=true
MAIL_SSL_TLS=false
MAIL_FROM_NAME=cafe booking
```

#### 5. Создать базу данных PostgreSQL

```sql
CREATE DATABASE cafe_booking;
CREATE USER your_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE cafe_booking TO your_user;
```

#### 6. Применить миграции

```bash
alembic -c src/alembic.ini upgrade head
```

#### 7. Запустить Redis (для Celery)

```bash
# Если Redis установлен локально
redis-server

# Или через Docker
docker run -d -p 6379:6379 redis:8-alpine
```

#### 8. Запустить Celery worker (в отдельном терминале)

```bash
celery -A src.celery_app.app.celery_app worker --loglevel=info
```

#### 9. Запустить Flower (опционально, для мониторинга)

```bash
celery -A src.celery_app.app.celery_app flower --port=5555
```

#### 10. Запустить сервер FastAPI

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Способ 2: Production запуск через Docker Compose (рекомендуемый)

Этот способ поднимает все сервисы: PostgreSQL, Redis, API, Celery worker, Flower и Nginx.

#### 1. Подготовка окружения

```bash
git clone https://github.com/Yandex-Practicum-Students/64_65_booking_seats_team_3.git
cd 64_65_booking_seats_team_3
```

#### 2. Создать файл `.env` в директории `infra/`

```bash
# PostgreSQL
POSTGRES_USER=booking_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=cafe_booking
POSTGRES_SERVER=db
POSTGRES_PORT=5432

# API
APP_TITLE=Система бронирования мест в кафе
APP_DESCRIPTION=API для бронирования столов в кафе
SECRET_KEY=your_super_secret_key_min_32_chars
ALGORITHM=HS256

# Первый суперпользователь
FIRST_SUPERUSER_LOGIN=admin@example.com
FIRST_SUPERUSER_PASSWORD=admin_password

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Celery (опционально, если нужно переопределить)
# CELERY_BROKER_URL=redis://redis:6379/0
# CELERY_RESULT_BACKEND=redis://redis:6379/0

# Email (настройте для продакшна)
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_STARTTLS=true
MAIL_SSL_TLS=false
MAIL_FROM_NAME=cafe booking
```

#### 3. Настройка SSL (для HTTPS)

Убедитесь, что у вас есть сертификаты Let's Encrypt для домена team3.ddns.net:

```bash
# Сертификаты должны лежать в:
/etc/letsencrypt/live/team3.ddns.net/fullchain.pem
/etc/letsencrypt/live/team3.ddns.net/privkey.pem
```

Если сертификатов нет, временно закомментируйте в `infra/nginx.conf` блок с HTTPS и используйте только HTTP.

#### 4. Собрать и запустить контейнеры

```bash
cd infra
docker-compose -f docker-compose.production.yml up -d --build
```

**Что произойдет:**

- `db` — PostgreSQL 17 с проверкой здоровья
- `redis` — Redis 8
- `api` — FastAPI приложение (через entrypoint.sh с миграциями)
- `celery_worker` — Celery worker для фоновых задач
- `flower` — Мониторинг Celery на порту 5555
- `nginx` — Reverse-proxy на 80/443 с раздачей медиа

#### 5. Проверка работы

```bash
# Статус контейнеров
docker-compose -f docker-compose.production.yml ps

# Логи API
docker-compose -f docker-compose.production.yml logs -f api

# Проверка эндпоинтов
curl https://team3.ddns.net/api/v1/health
```

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
curl -X POST http://localhost:8000/api/v1/booking \
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

| Сервис | Адрес доступа |
|--------|---------------|
| **Flower** (мониторинг Celery) | `https://team3.ddns.net:5555` или `http://localhost:5555` |
| **Логи всех сервисов** | `docker-compose -f infra/docker-compose.production.yml logs -f` |
| **Логи только API** | `docker logs cafe_booking-api-1` |

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

Проект покрыт тестами с использованием `pytest`.

```bash
# Локальный запуск тестов
pytest -v

# Запуск тестов в Docker (предварительно создав тестовую БД)
docker exec cafe_booking-api-1 pytest -v
```

---

## Структура исходного кода

```text
src/
├── auth/           # Аутентификация и JWT токены
├── cafes/          # Управление кафе
├── tables/         # Управление столами
├── slots/          # Управление временными слотами
├── bookings/       # Управление бронированиями
├── users/          # Управление пользователями
├── media/          # Работа с изображениями
├── celery_app/     # Конфигурация Celery и задачи
│   ├── app.py      # Инициализация Celery
│   └── tasks/      # Фоновые задачи
├── core/           # Конфигурация и утилиты (config, logger, middleware)
├── db/             # Настройка БД, сессии, first_admin
└── main.py         # Точка входа
```

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
