from datetime import datetime, timedelta

from src.bookings.models import Booking, TableSlot
from src.celery_app.tasks.booking_notif_tasks import (
    notify_admin_booking_created,
    notify_admin_booking_updated,
    notify_user_slot_status_changed,
    send_booking_reminder,
)
from src.core.logger import get_logger

logger = get_logger(__name__)


def schedule_notifications_on_create(booking: Booking) -> None:
    """Планирует уведомления при создании бронирования."""
    for manager in booking.cafe.managers:
        if manager.email:
            notify_admin_booking_created.delay(
                booking_id=str(booking.id),
                cafe_name=booking.cafe.name,
                admin_email=manager.email,
                user_name=booking.user.username,
                booking_date=str(booking.booking_date),
                guest_number=booking.guest_number,
            )
            logger.debug(
                'Запланировано уведомление менеджеру %s о бронировании %s',
                manager.email,
                booking.id,
            )
        else:
            logger.debug(
                'У менеджера %s не указан email, оповещение невозможно.',
                manager.id,
            )

    if booking.user.email and booking.tables_slots:
        first_slot = booking.tables_slots[0].slot
        booking_datetime = datetime.combine(
            booking.booking_date,
            first_slot.start_time,
        )
        reminder_time = booking_datetime - timedelta(hours=1)

        if reminder_time > datetime.now():
            send_booking_reminder.apply_async(
                kwargs=dict(
                    booking_id=str(booking.id),
                    user_email=booking.user.email,
                    cafe_name=booking.cafe.name,
                    booking_date=str(booking.booking_date),
                    slot_time=str(first_slot.start_time),
                ),
                eta=reminder_time,
            )
            logger.debug(
                'Запланировано напоминание пользователю %s '
                'о бронировании %s на %s',
                booking.user.email,
                booking.id,
                reminder_time,
            )
    if not booking.user.email:
        logger.debug(
            'У пользователя %s не указан email, оповещение невозможно.',
            booking.user.id,
        )


def schedule_notifications_on_update(booking: Booking) -> None:
    """Планирует уведомления при обновлении бронирования."""
    for manager in booking.cafe.managers:
        if manager.email:
            notify_admin_booking_updated.delay(
                booking_id=str(booking.id),
                cafe_name=booking.cafe.name,
                admin_email=manager.email,
                user_name=booking.user.username,
                booking_date=str(booking.booking_date),
                new_status=str(booking.status),
            )
            logger.debug(
                'Запланировано уведомление менеджеру %s '
                'об изменении бронирования %s',
                manager.email,
                booking.id,
            )


def schedule_notifications_on_slot_status_change(
    affected_table_slots: list[TableSlot],
    reason: str,
) -> None:
    """Уведомляет пользователей, что их забронированный стол/слот отключен.

    Вызывается перед деактивацией Slot/Table для тех TableSlot,
    которые уже привязаны к активным бронированиям (booking_id заполнен),
    так как такие записи НЕ деактивируются автоматически.

    Args:
        affected_table_slots: Список TableSlot с загруженным booking,
            table и slot, попадающих под отключение.
        reason: Текстовое описание причины (например,
            'Стол временно недоступен' или 'Слот отключен').

    """
    for table_slot in affected_table_slots:
        booking: Booking | None = table_slot.booking
        if booking is None or not booking.is_active:
            continue

        table_label = (
            table_slot.table.description
            or f'стол на {table_slot.table.seat_number} мест'
        )

        if booking.user.email:
            notify_user_slot_status_changed.delay(
                booking_id=str(booking.id),
                user_email=booking.user.email,
                cafe_name=booking.cafe.name,
                booking_date=str(table_slot.booking_date),
                slot_time=str(table_slot.slot.start_time),
                table_label=table_label,
                reason=reason,
            )
            logger.debug(
                'Запланировано уведомление пользователю %s об изменении '
                'статуса стола/слота для бронирования %s',
                booking.user.email,
                booking.id,
            )
        else:
            logger.debug(
                'У пользователя %s не указан email, '
                'оповещение об изменении статуса стола/слота невозможно.',
                booking.user.id,
            )

        for manager in booking.cafe.managers:
            if manager.email:
                notify_admin_booking_updated.delay(
                    booking_id=str(booking.id),
                    cafe_name=booking.cafe.name,
                    admin_email=manager.email,
                    user_name=booking.user.username,
                    booking_date=str(table_slot.booking_date),
                    new_status=reason,
                )
