import asyncio

from fastapi_mail import FastMail, MessageSchema, MessageType

from src.notifications.config import mail_config


async def _send_email(
    recipient: str,
    subject: str,
    body: str,
) -> None:
    """Асинхронная отправка email."""
    message = MessageSchema(
        subject=subject,
        recipients=[recipient],
        body=body,
        subtype=MessageType.plain,
    )
    fm = FastMail(mail_config)
    await fm.send_message(message)


def send_email_sync(
    recipient: str,
    subject: str,
    body: str,
) -> None:
    """Синхронная обертка для отправки email для Celery."""
    asyncio.run(_send_email(recipient, subject, body))
