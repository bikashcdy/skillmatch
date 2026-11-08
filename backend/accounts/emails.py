"""Account e-mails: password reset and recruiter approval."""

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from core.mail import SITE_URL, send

from .models import User


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
