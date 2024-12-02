import logging

from celery import shared_task

from .services.handler_emails import send_mail


logger = logging.getLogger(__name__)


@shared_task
def monitor_mail_forever():
    from .services.handler_emails import handle_incoming_emails

    handle_incoming_emails()

@shared_task
def send_mail_background(reply_to_email, subject, body, message_id):
    send_mail(
        reply_to_email,
        subject,
        body,
        message_id,
    )
    logger.debug("Сообщение отправлено")
