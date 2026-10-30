"""Email notifications. Works with no setup: emails are printed in the backend terminal.

To send real emails, add the EMAIL_* lines from README.md to config/settings.py.
Every function swallows errors so a mail problem can never break applying or hiring.
"""

import logging

from django.conf import settings
from django.core.mail import EmailMessage, get_connection

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import User

log = logging.getLogger(__name__)

STRONG_MATCH = 80.0  # tell the recruiter
SMTP_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
SITE_URL = getattr(settings, "FRONTEND_URL", "http://localhost:5173")


def _connection():
    # No SMTP login configured -> print emails in the terminal instead of failing.
    if settings.EMAIL_BACKEND == SMTP_BACKEND and not getattr(settings, "EMAIL_HOST_USER", ""):
        return get_connection("django.core.mail.backends.console.EmailBackend")
    return get_connection(timeout=10) if settings.EMAIL_BACKEND == SMTP_BACKEND else get_connection()


def _sender():
    return getattr(settings, "DEFAULT_FROM_EMAIL", None) or "JobMitra <noreply@localhost>"


def _from_recruiter(job):
    """Show the recruiter's company as the sender; replies go to the recruiter's own email."""
    rec = job.recruiter
    name = (job.company or rec.company_name or rec.username).replace('"', "").replace("<", "").replace(">", "")
    address = _sender().split("<")[-1].rstrip(">")
    return f"{name} via JobMitra <{address}>", ([rec.email] if rec.email else None)


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


def application_decision(application):
    """Candidate: you were selected / not selected."""
    job, cand = application.job, application.candidate
    if application.status == "selected":
        subject = f"Good news: you were selected for {job.title}"
        body = (f"Hello {cand.username},\n\n{job.company} has selected you for the {job.title} position "
                f"({application.match_percentage}% match).\n")
    elif application.status == "rejected":
        subject = f"Update on your application: {job.title}"
        body = (f"Hello {cand.username},\n\nThank you for applying to {job.title} at {job.company}. "
                "They decided not to move forward this time. Check your Career plan for skills that can "
                "raise your match for similar jobs.\n")
    else:
        return False
    if application.recruiter_note:
        body += f"\nMessage from the recruiter:\n\"{application.recruiter_note}\"\n"
    sender, reply = _from_recruiter(job)
    body += (f"\nYou can reply to this email to reach {job.company} directly"
             f"{' (' + job.recruiter.email + ')' if job.recruiter.email else ''}.\n"
             f"Open your applications: {SITE_URL}/my-applications\n\n- {job.company} via JobMitra")
    return send(cand.email, subject, body, sender, reply)


def strong_matches(applications):
    """Recruiters: ONE email per recruiter listing every strong candidate (80%+) from this action."""
    by_recruiter = {}
    for app in applications:
        if app.match_percentage >= STRONG_MATCH:
            by_recruiter.setdefault(app.job.recruiter, []).append(app)
    sent = 0
    for rec, apps in by_recruiter.items():
        cand = apps[0].candidate
        lines = "\n".join(
            f"- {a.job.title}: {a.match_percentage}% (matched: {', '.join(a.matched_skills) or '-'})  {SITE_URL}/recruiter/jobs/{a.job_id}"
            for a in apps
        )
        body = (f"Hello {rec.username},\n\n{cand.username} applied with a strong match ({STRONG_MATCH:.0f}%+) to "
                f"{'your job' if len(apps) == 1 else str(len(apps)) + ' of your jobs'}:\n\n{lines}\n\n"
                f"Reply to this email to contact the candidate.\n\n- JobMitra")
        subject = (f"Strong match ({apps[0].match_percentage}%) for {apps[0].job.title}" if len(apps) == 1
                   else f"{len(apps)} strong matches from {cand.username}")
        sent += send(rec.email, subject, body, reply_to=[cand.email] if cand.email else None)
    return sent


def recruiter_message(application):
    """Candidate: the recruiter wrote you a note."""
    job, cand = application.job, application.candidate
    sender, reply = _from_recruiter(job)
    body = (f"Hello {cand.username},\n\n{job.company} sent you a message about {job.title}:\n\n"
            f"\"{application.recruiter_note}\"\n\nReply to this email to answer them directly.\n"
            f"See it here: {SITE_URL}/my-applications\n\n- {job.company} via JobMitra")
    return send(cand.email, f"New message from {job.company}", body, sender, reply)


# ---------- accounts: password reset, recruiter approval ----------
class _Token(PasswordResetTokenGenerator):
    """Password reset links are signed with a separate salt and expire after 3 days."""


class ResetTokenGenerator(_Token):
    key_salt = "jobmitra.password-reset"


reset_tokens = ResetTokenGenerator()


def _link(path, user, generator):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    return f"{SITE_URL}{path}?uid={uid}&token={generator.make_token(user)}"


def password_reset_email(user):
    link = _link("/reset-password", user, reset_tokens)
    body = (f"Hello {user.username},\n\nSomeone asked to reset your JobMitra password. Open this link to choose a new one:\n\n"
            f"{link}\n\nThe link works for 3 days. If it was not you, ignore this email; your password stays the same.\n\n- JobMitra")
    return send(user.email, "Reset your JobMitra password", body)


def recruiter_waiting(recruiter):
    """Tell every admin that a recruiter wants approval."""
    for admin in User.objects.filter(role=User.ADMIN, is_active=True).exclude(email=""):
        send(admin.email, f"Recruiter waiting for approval: {recruiter.company_name or recruiter.username}",
             f"{recruiter.username} ({recruiter.email}) registered as a recruiter for "
             f"\"{recruiter.company_name}\".\n\nReview in the admin dashboard: {SITE_URL}/admin\n\n- JobMitra")


def recruiter_decision(recruiter):
    if recruiter.is_approved:
        send(recruiter.email, "Your JobMitra recruiter account is approved",
             f"Hello {recruiter.username},\n\nYour account was approved. You can now post jobs: {SITE_URL}/recruiter\n\n- JobMitra")
    else:
        send(recruiter.email, "Your JobMitra recruiter account was not approved",
             f"Hello {recruiter.username},\n\nYour recruiter account is not approved at the moment. "
             "Reply to this email if you think this is a mistake.\n\n- JobMitra")
