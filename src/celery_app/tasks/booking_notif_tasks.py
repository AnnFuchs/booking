from celery import Task, shared_task

from src.core.logger import get_logger
from src.notifications.email import send_email_sync

logger = get_logger(__name__)


@shared_task(
    name='notify_admin_booking_created',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def notify_admin_booking_created(
    self: Task,
    booking_id: str,
    cafe_name: str,
    admin_email: str,
    user_name: str,
    booking_date: str,
    guest_number: int,
) -> None:
    """Оповещение о создании бронирования для менеджмента."""
    try:
        subject = f'Новое бронирование в {cafe_name}'
        body = (
            f'Новое бронирование #{booking_id}\n\n'
            f'Кафе: {cafe_name}\n'
            f'Пользователь: {user_name}\n'
            f'Дата: {booking_date}\n'
            f'Количество гостей: {guest_number}\n'
        )
        send_email_sync(admin_email, subject, body)
        logger.debug(
            'Отправлено уведомление администратору %s о бронировании %s',
            admin_email,
            booking_id,
        )
    except Exception as exc:
        logger.error(
            'Ошибка отправки уведомления для бронирования %s: %s',
            booking_id,
            exc,
        )
        raise self.retry(exc=exc)


@shared_task(
    name='notify_admin_booking_updated',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def notify_admin_booking_updated(
    self: Task,
    booking_id: str,
    cafe_name: str,
    admin_email: str,
    user_name: str,
    booking_date: str,
    new_status: str,
) -> None:
    """Оповещение об обновлении бронирования для менеджмента."""
    try:
        subject = f'Изменение бронирования в {cafe_name}'
        body = (
            f'Бронирование #{booking_id} было изменено\n\n'
            f'Кафе: {cafe_name}\n'
            f'Пользователь: {user_name}\n'
            f'Дата: {booking_date}\n'
            f'Новый статус: {new_status}\n'
        )
        send_email_sync(admin_email, subject, body)
        logger.debug(
            'Отправлено уведомление администратору %s об изменении '
            'бронирования %s',
            admin_email,
            booking_id,
        )
    except Exception as exc:
        logger.error(
            'Ошибка отправки уведомления для бронирования %s: %s',
            booking_id,
            exc,
        )
        raise self.retry(exc=exc)


@shared_task(
    name='send_booking_reminder',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_booking_reminder(
    self: Task,
    booking_id: str,
    user_email: str,
    cafe_name: str,
    booking_date: str,
    slot_time: str,
) -> None:
    """Оповещение пользователя о бронировании."""
    try:
        subject = f'Напоминание о бронировании в {cafe_name}'
        body = (
            f'Напоминаем о вашем бронировании #{booking_id}\n\n'
            f'Кафе: {cafe_name}\n'
            f'Дата: {booking_date}\n'
            f'Время: {slot_time}\n\n'
            f'Ждём вас!'
        )
        send_email_sync(user_email, subject, body)
        logger.debug(
            'Отправлено напоминание пользователю о бронировании %s',
            booking_id,
        )
    except Exception as exc:
        logger.error(
            'Ошибка отправки напоминания для бронирования %s: %s',
            booking_id,
            exc,
        )
        raise self.retry(exc=exc)
