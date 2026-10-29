"""Email notifications. Works with no setup: emails are printed in the backend terminal.

To send real emails, add the EMAIL_* lines from README.md to config/settings.py.
Every function swallows errors so a mail problem can never break applying or hiring.
"""

import logging

from django.conf import settings
from django.core.mail import EmailMessage, get_connection

from .matching import score_match
from .models import Job, User

log = logging.getLogger(__name__)

STRONG_MATCH = 80.0  # tell the recruiter
ALERT_MATCH = 70.0  # tell the candidate about a new job
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


def strong_match(application):
    """Recruiter: a strong candidate (80%+) applied."""
    if application.match_percentage < STRONG_MATCH:
        return False
    job, cand = application.job, application.candidate
    body = (f"Hello {job.recruiter.username},\n\n{cand.username} just applied to your job \"{job.title}\" "
            f"with a {application.match_percentage}% match.\n"
            f"Matched skills: {', '.join(application.matched_skills) or '-'}\n"
            f"Missing skills: {', '.join(application.missing_skills) or '-'}\n\n"
            f"Review the ranked candidates: {SITE_URL}/recruiter/jobs/{job.id}\n\n- JobMitra")
    return send(job.recruiter.email, f"Strong match ({application.match_percentage}%) for {job.title}", body,
                reply_to=[cand.email] if cand.email else None)


def recruiter_message(application):
    """Candidate: the recruiter wrote you a note."""
    job, cand = application.job, application.candidate
    sender, reply = _from_recruiter(job)
    body = (f"Hello {cand.username},\n\n{job.company} sent you a message about {job.title}:\n\n"
            f"\"{application.recruiter_note}\"\n\nReply to this email to answer them directly.\n"
            f"See it here: {SITE_URL}/my-applications\n\n- {job.company} via JobMitra")
    return send(cand.email, f"New message from {job.company}", body, sender, reply)


def new_job_alerts(job):
    """Candidates whose latest resume matches the new job by 70% or more."""
    sent = 0
    people = User.objects.filter(role=User.CANDIDATE, is_active=True, email_alerts=True).exclude(email="")
    for user in people:
        resume = user.resumes.order_by("-uploaded_at").first()
        if not resume:
            continue
        pct = score_match(resume, job)["match_percentage"]
        if pct >= ALERT_MATCH:
            body = (f"Hello {user.username},\n\nA new job matches your resume by {pct}%:\n\n"
                    f"{job.title} at {job.company} ({job.location or 'location not set'})\n\n"
                    f"View and apply: {SITE_URL}/jobs\n\n"
                    f"(Turn off job alerts on the Jobs page.)\n\n- JobMitra")
            sent += send(user.email, f"New job for you: {job.title} ({pct}% match)", body)
    return sent
