"""Shared e-mail sending. Works with no setup: emails are printed in the backend terminal.

To send real emails, add the EMAIL_* lines from README.md to config/settings.py.
Every function swallows errors so a mail problem can never break applying or hiring.
"""

import logging

from django.conf import settings
from django.core.mail import EmailMessage, get_connection

log = logging.getLogger(__name__)


SMTP_BACKEND = "django.core.mail.backends.smtp.EmailBackend"


SITE_URL = getattr(settings, "FRONTEND_URL", "http://localhost:5173")


def _connection():
    # No SMTP login configured -> print emails in the terminal instead of failing.
    if settings.EMAIL_BACKEND == SMTP_BACKEND and not getattr(settings, "EMAIL_HOST_USER", ""):
        return get_connection("django.core.mail.backends.console.EmailBackend")
    return get_connection(timeout=10) if settings.EMAIL_BACKEND == SMTP_BACKEND else get_connection()


def _sender():
    return getattr(settings, "DEFAULT_FROM_EMAIL", None) or "JobMitra <noreply@localhost>"


def send(to, subject, body, from_email=None, reply_to=None):
    if not to:
        return False
    try:
        EmailMessage(subject, body, from_email or _sender(), [to],
                     reply_to=reply_to, connection=_connection()).send()
        return True
    except Exception:  # noqa: BLE001 - never break the request because of email
        log.exception("Could not send email to %s", to)
        return False
