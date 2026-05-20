import os
import smtplib
from email.message import EmailMessage

SMTP_HOST = os.environ.get('SMTP_HOST')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
SMTP_FROM_EMAIL = os.environ.get('SMTP_FROM_EMAIL', SMTP_USERNAME or 'no-reply@biblequiz.com')


def send_email(subject: str, body: str, to_email: str):
    """Send a simple plain-text email using SMTP."""
    if not SMTP_HOST or not SMTP_USERNAME or not SMTP_PASSWORD:
        return False, 'SMTP is not configured. Set SMTP_HOST, SMTP_USERNAME, and SMTP_PASSWORD.'

    message = EmailMessage()
    message['Subject'] = subject
    message['From'] = SMTP_FROM_EMAIL
    message['To'] = to_email
    message.set_content(body)

    try:
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
                smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
                smtp.starttls()
                smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
                smtp.send_message(message)
        return True, None
    except Exception as e:
        return False, str(e)
