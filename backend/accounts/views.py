from django.shortcuts import get_object_or_404
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from jobs.models import Job
from profiles.services import update_preferences

from . import emails
from . import validators as V
from .models import User
from .permissions import IsAdminRole
from .serializers import RegisterSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        if user.role == User.RECRUITER:
            emails.recruiter_waiting(user)
        data = dict(ser.data)
        data["waiting_for_approval"] = not user.is_approved
        return Response(data, status=201)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def check_availability(request):
    """Live check while typing in the sign-up form: is this username / email free and valid?"""
    out = {}
    if "username" in request.data:
        u = (request.data.get("username") or "").strip()
        errors = V.username_errors(u)
        if not errors and User.objects.filter(username__iexact=u).exists():
            errors = ["This username is already taken."]
        out["username"] = errors
    if "email" in request.data:
        e = (request.data.get("email") or "").strip().lower()
        errors = V.email_errors(e)
        if not errors and User.objects.filter(email__iexact=e).exists():
            errors = ["An account with this email already exists."]
        out["email"] = errors
    return Response(out)


def _user_from_uid(uid):
    try:
        return User.objects.get(pk=force_str(urlsafe_base64_decode(uid or "")))
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        return None


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def forgot_password(request):
    email = (request.data.get("email") or "").strip()
    if email:
        for user in User.objects.filter(email__iexact=email, is_active=True):
            emails.password_reset_email(user)
    return Response({"detail": "If that email has an account, a reset link is on its way."})  # never reveal who exists


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def reset_password(request):
    user = _user_from_uid(request.data.get("uid"))
    password = request.data.get("password") or ""
    if not user or not emails.reset_tokens.check_token(user, request.data.get("token") or ""):
        return Response({"detail": "This link is invalid or has expired. Ask for a new reset email."}, status=400)
    errors = V.password_errors(password, user.username, user.email)
    if errors:
        return Response({"detail": " ".join(errors)}, status=400)
    user.set_password(password)
    user.save(update_fields=["password"])
    return Response({"detail": "Password changed. You can log in now."})


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    u = request.user
    if not u.check_password(request.data.get("old_password") or ""):
        return Response({"detail": "Your current password is not correct."}, status=400)
    errors = V.password_errors(request.data.get("new_password") or "", u.username, u.email)
    if errors:
        return Response({"detail": " ".join(errors)}, status=400)
    u.set_password(request.data["new_password"])
    u.save(update_fields=["password"])
    return Response({"detail": "Password changed."})


def _me(u):
    return {
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "role": u.role,
        "company_name": u.company_name,
        "is_approved": u.is_approved,
        "preferred_location": u.preferred_location,
        "preferred_job_type": u.preferred_job_type,
    }


@api_view(["GET", "PATCH"])
@permission_classes([permissions.IsAuthenticated])
def me(request):
    u = request.user
    if request.method == "PATCH":
        if "email" in request.data:
            email = (request.data.get("email") or "").strip().lower()
            errors = V.email_errors(email)
            if not errors and User.objects.filter(email__iexact=email).exclude(pk=u.pk).exists():
                errors = ["An account with this email already exists."]
            if errors:
                return Response({"email": errors}, status=400)
            u.email = email
            u.save(update_fields=["email"])
        if u.role == User.CANDIDATE and ("preferred_location" in request.data or "preferred_job_type" in request.data):
            errors = update_preferences(u, request.data)
            if errors:
                return Response(errors, status=400)
        if u.role == User.RECRUITER and "company_name" in request.data:
            errors = V.company_errors(request.data.get("company_name"))
            if errors:
                return Response({"company_name": errors}, status=400)
            u.company_name = request.data["company_name"].strip()
            u.save(update_fields=["company_name"])
            Job.objects.filter(recruiter=u).update(company=u.company_name)
    return Response(_me(u))


class AdminUserListView(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    queryset = User.objects.all().order_by("-date_joined")

    def list(self, request, *args, **kwargs):
        data = [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "is_approved": u.is_approved,
                "company_name": u.company_name,
                "date_joined": u.date_joined,
            }
            for u in self.get_queryset()
        ]
        return Response(data)


@api_view(["POST"])
@permission_classes([IsAdminRole])
def toggle_user(request, user_id):
    u = get_object_or_404(User, pk=user_id)
    if u.pk == request.user.pk:
        return Response({"detail": "You cannot deactivate your own account."}, status=400)
    u.is_active = not u.is_active
    u.save(update_fields=["is_active"])
    return Response({"id": u.id, "is_active": u.is_active})


@api_view(["POST"])
@permission_classes([IsAdminRole])
def approve_recruiter(request, user_id):
    """Body {"approved": true|false}. Un-approving hides the recruiter's jobs from candidates."""
    u = get_object_or_404(User, pk=user_id, role=User.RECRUITER)
    u.is_approved = str(request.data.get("approved", True)).lower() in ("1", "true", "yes")
    u.save(update_fields=["is_approved"])
    emails.recruiter_decision(u)
    return Response({"id": u.id, "is_approved": u.is_approved})
