import logging
import imaplib
import smtplib
import email
from email.utils import parseaddr
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from django.db import transaction
from django.forms import model_to_dict
from django.db.models import Q
from django.conf import settings

from ..models import Tickets

logger = logging.getLogger(__name__)


def connect_to_mailbox():
    """Устанавливает соединение с почтовым ящиком."""
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(settings.EMAIL, settings.PASSWORD_EMAIL)
        mail.select("INBOX")
        return mail
    except Exception as e:
        logger.error(f"Ошибка подключения к почтовому ящику: {e}")
        raise


def get_latest_email_id(mail):
    """Возвращает ID последнего письма."""
    try:
        result, data = mail.search(None, "UNSEEN")
        if result != "OK" or not data[0]:
            logger.warning("Папка пуста или произошла ошибка при поиске писем.")
            return None
        return data[0].split()[-1]  # Последний ID письма
    except Exception as e:
        logger.error(f"Ошибка при получении списка писем: {e}")
        return None


def fetch_email(mail, email_id):
    """Извлекает письмо по ID."""
    try:
        result, data = mail.fetch(email_id, "(RFC822)")
        if result != "OK" or not data:
            logger.error(f"Ошибка получения письма с ID {email_id}.")
            return None
        return data[0][1]
    except Exception as e:
        logger.error(f"Ошибка при извлечении письма: {e}")
        return None


def decode_email(raw_email):
    """Декодирует письмо из байтового представления."""
    try:
        return raw_email.decode("utf-8")
    except UnicodeDecodeError:
        return raw_email.decode("latin1")


def parse_email_content(raw_email_string):
    """Парсит содержимое письма."""
    try:
        email_message = email.message_from_string(raw_email_string)
        subject = decode_subject(email_message)
        sender = parseaddr(email_message["From"])[1]
        body = get_email_body(email_message)
        return subject, sender, body, email_message
    except Exception as e:
        logger.error(f"Ошибка при разборе содержимого письма: {e}")
        return None, None, None, None


def decode_subject(email_message):
    """Декодирует заголовок 'Subject'."""
    try:
        decoded_parts = decode_header(email_message["Subject"])
        return "".join(
            (
                part[0].decode(part[1] or "utf-8")
                if isinstance(part[0], bytes)
                else part[0]
            )
            for part in decoded_parts
        )
    except Exception as e:
        logger.warning(f"Ошибка при декодировании заголовка: {e}")
        return "Без темы"


def get_email_body(email_message):
    """Извлекает тело письма."""
    try:
        if email_message.is_multipart():
            for part in email_message.get_payload():
                if (
                    part.get_content_type() == "text/plain"
                    and "attachment" not in part.get("Content-Disposition", "")
                ):
                    return part.get_payload(decode=True).decode(
                        "utf-8", errors="ignore"
                    )
        else:
            return email_message.get_payload(decode=True).decode(
                "utf-8", errors="ignore"
            )
    except Exception as e:
        logger.warning(f"Ошибка при извлечении тела письма: {e}")
    return ""


def process_new_email(mail):
    """Проверяет и обрабатывает новое письмо."""
    latest_email_id = get_latest_email_id(mail)
    if not latest_email_id:
        logger.info("Нет новых писем для обработки.")
        return None

    latest_email_id = latest_email_id.decode("utf-8")
    if Tickets.objects.filter(id_mails__contains=[latest_email_id]).exists():
        logger.info(f"Письмо с ID {latest_email_id} уже обработано.")
        return None

    raw_email = fetch_email(mail, latest_email_id)
    if not raw_email:
        return None

    raw_email_string = decode_email(raw_email)
    subject, sender, body, email_message = parse_email_content(raw_email_string)

    soup = BeautifulSoup(body, "html.parser")
    body = soup.get_text()
    if sender != settings.EMAIL:
        logger.debug(f"Subject: {subject}")
        logger.debug(f"From: {sender}")
        logger.debug(f"Date: {email_message['Date']}")
        logger.debug(f"Body: {body}")
        logger.debug(f"Message-ID: {email_message['Message-ID']}")
        return {
            "subject": subject,
            "email": sender,
            "id_mail": latest_email_id,
            "body": body,
            "message_id": email_message["Message-ID"],
        }
    else:
        logger.info("Письмо отправлено самим себе. Пропуск обработки.")
        return None


def create_or_update_ticket(subject, email, id_mail, body, message_id):
    """Создает или обновляет обращение в базе данных."""
    try:
        ticket = Tickets.objects.filter(
            Q(email=email) & (Q(status="new") | Q(status="in_process"))
        )
        if ticket.exists():
            ticket = ticket.first()
            logger.debug(body)
            logger.debug(ticket.bodies)
            logger.debug(body in ticket.bodies)
            if id_mail not in ticket.id_mails:
                ticket.id_mails.append(id_mail)
                ticket.save()
            if body not in ticket.bodies:
                ticket.bodies.append(body)
                ticket.save()
                logger.info("Добавлено новое сообщение в обращение")

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"ticket_message_{ticket.id}",
                {
                    "type": "add_message_in_ticket",
                    "ticket_message": ticket.bodies[-1],
                },
            )
        else:
            with transaction.atomic():
                ticket = Tickets.objects.create(
                    subject=subject,
                    email=email,
                    bodies=[body.strip()],
                    id_mails=[id_mail],
                    messages_id=[message_id],
                )
                logger.info(f"Обращение успешно создано - {ticket.created_at}")
                return ticket
    except Exception as e:
        logger.error(f"Ошибка при создании обращения: {e}")


def send_mail(reply_to_email, subject, body, message_id):
    """Отправляет письмо."""
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    try:
        logger.debug(
            f"Инициализация отправки письма: To={reply_to_email}, Subject={subject}"
        )

        msg = MIMEMultipart()
        msg["From"] = settings.EMAIL
        msg["To"] = reply_to_email
        msg["Subject"] = subject
        msg["In-Reply-To"] = message_id
        msg["References"] = message_id

        msg.attach(MIMEText(body, "plain"))

        logger.debug(f"Собранное письмо:\n{msg.as_string()}")

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(settings.EMAIL, settings.PASSWORD_EMAIL)

        server.sendmail(settings.EMAIL, reply_to_email, msg.as_string())
        server.quit()
        logger.info("Письмо успешно отправлено")
    except Exception as e:
        logger.error(f"Ошибка при отправке письма: {e}")
        raise


def handle_incoming_emails():
    """Основная функция чтения и обработки писем."""
    mail = connect_to_mailbox()
    try:
        if ticket_data := process_new_email(mail):
            if db_activity := create_or_update_ticket(**ticket_data):
                created_at = db_activity.created_at.strftime("%d.%m.%Y, %H:%M:%S")
                ticket_serializer = model_to_dict(db_activity)
                ticket_serializer["created_at"] = created_at
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    "ticket_list",
                    {
                        "type": "add_ticket",
                        "ticket": ticket_serializer,
                    },
                )
                send_mail(
                    reply_to_email=ticket_data["email"],
                    subject=f"Re: {ticket_data['subject']}",
                    body="Мы свяжемся с вами в ближайшее время.",
                    message_id=ticket_data["message_id"],
                )
    except Exception as e:
        logger.error(f"Ошибка при обработке писем: {e}")
    finally:
        mail.logout()
