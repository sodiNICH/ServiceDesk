import logging

from ..tasks import send_mail_background


logger = logging.getLogger(__name__)


def start_tasks_send_mail(ticket, subject, body):
    """
    Запускает Celery таску с отправкой письма.
    """
    try:
        send_mail_background.delay(
            reply_to_email=ticket.email,
            subject=subject,
            body=body,
            message_id=ticket.messages_id[-1],
        )
        logger.info(f"Письмо отправлено для обращения ID {ticket.id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке письма для обращения ID {ticket.id}: {e}")
