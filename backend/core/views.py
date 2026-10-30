import datetime
import os

from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .matching import (
    ALLOWED_EXTENSIONS,
    UnreadableResume,
    normalize_skill,
    SKILLS,
    parse_resume,
    refresh_skills,
    score_match,
)
from .models import Application, Job, Resume, User, nepal_today
from .serializers import (
    ApplicationSerializer,
    JobSerializer,
    RegisterSerializer,
    ResumeSerializer,
)
from . import notifications
from . import validators as V
from .recommendations import NEPAL_CITIES, build_recommendations, resume_health
from .services import apply_to_job, select_best_candidate, set_application_status


class IsRole(permissions.BasePermission):
    roles = ()

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in self.roles


class IsRecruiter(IsRole):
    roles = (User.RECRUITER,)


class IsCandidate(IsRole):
    roles = (User.CANDIDATE,)


class IsAdminRole(IsRole):
    roles = (User.ADMIN,)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        if user.role == User.RECRUITER:
            notifications.recruiter_waiting(user)
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
            notifications.password_reset_email(user)
    return Response({"detail": "If that email has an account, a reset link is on its way."})  # never reveal who exists


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def reset_password(request):
    user = _user_from_uid(request.data.get("uid"))
    password = request.data.get("password") or ""
    if not user or not notifications.reset_tokens.check_token(user, request.data.get("token") or ""):
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
        if u.role == User.RECRUITER and "company_name" in request.data:
            errors = V.company_errors(request.data.get("company_name"))
            if errors:
                return Response({"company_name": errors}, status=400)
            u.company_name = request.data["company_name"].strip()
            u.save(update_fields=["company_name"])
            Job.objects.filter(recruiter=u).update(company=u.company_name)
    return Response(_me(u))


# ---------- Jobs ----------
class JobListView(generics.ListAPIView):
    """Open jobs. Filters: ?q= (title/company/skill), ?location=, ?skill=."""

    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        p = self.request.query_params
        qs = Job.active().order_by("-created_at")
        loc = (p.get("location") or "").strip()
        if loc:
            qs = qs.filter(location__icontains=loc)
        jobs = list(qs)
        q = (p.get("q") or "").strip().lower()
        if q:
            canon = normalize_skill(q)
            jobs = [
                j
                for j in jobs
                if q in j.title.lower()
                or q in j.company.lower()
                or q in (j.description or "").lower()
                or canon in j.required_skills
                or any(q in sk for sk in j.required_skills)
            ]
        skill = (p.get("skill") or "").strip()
        if skill:
            canon = normalize_skill(skill)
            jobs = [j for j in jobs if canon in j.required_skills]
        jt = (p.get("job_type") or "").strip()
        if jt:
            jobs = [j for j in jobs if j.job_type == jt]
        try:
            min_salary = int(p.get("min_salary") or 0)
        except ValueError:
            min_salary = 0
        if min_salary:  # keep jobs that can pay at least this much; hide jobs with no salary shown
            jobs = [j for j in jobs if (j.salary_max or j.salary_min or 0) >= min_salary]
        return jobs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        u = self.request.user
        if u.role == User.CANDIDATE:
            ctx["my_apps"] = {a.job_id: a for a in Application.objects.filter(candidate=u)}
            resume = u.resumes.order_by("-uploaded_at").first()
            if resume:
                refresh_skills(resume)
                ctx["match_map"] = {
                    j.id: score_match(resume, j)["match_percentage"]
                    for j in Job.active()
                }
        return ctx


class JobDetailView(generics.RetrieveAPIView):
    """Full details of one active job, with the candidate's own match breakdown."""

    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = "job_id"

    def get_queryset(self):
        return Job.active()

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        u = self.request.user
        if u.role == User.CANDIDATE:
            job = self.get_object()
            ctx["my_apps"] = {a.job_id: a for a in Application.objects.filter(candidate=u, job=job)}
            resume = u.resumes.order_by("-uploaded_at").first()
            if resume:
                refresh_skills(resume)
                detail = score_match(resume, job)
                ctx["match_map"] = {job.id: detail["match_percentage"]}
                ctx["match_detail"] = {job.id: detail}
        return ctx


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def job_meta(request):
    """Data for the search bar: locations, trending skills and headline numbers."""
    jobs = list(Job.active())
    skills = {}
    for j in jobs:
        for sk in j.required_skills:
            skills[sk] = skills.get(sk, 0) + 1
    ranked = sorted(skills.items(), key=lambda x: (-x[1], x[0]))
    return Response(
        {
            "skills": [{"name": n, "count": c} for n, c in ranked],
            "cities": NEPAL_CITIES,  # only used by the recruiter's "post a job" dropdown
            "catalog": sorted(SKILLS),
            "stats": {
                "jobs": len(jobs),
                "companies": len({j.company for j in jobs}),
            },
        }
    )


class RecruiterJobView(generics.ListCreateAPIView):
    serializer_class = JobSerializer
    permission_classes = [IsRecruiter]

    def get_queryset(self):
        return Job.objects.filter(recruiter=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        u = self.request.user
        if not u.is_approved:
            raise PermissionDenied("Your recruiter account is waiting for admin approval. You can post jobs once it is approved.")
        extra = {}
        if not serializer.validated_data.get("expires_at"):
            extra["expires_at"] = nepal_today() + datetime.timedelta(days=30)  # default: 30 days
        serializer.save(recruiter=u, company=u.company_name or u.username, **extra)


class RecruiterJobDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = JobSerializer
    permission_classes = [IsRecruiter]

    def get_queryset(self):
        return Job.objects.filter(recruiter=self.request.user)


@api_view(["GET"])
@permission_classes([IsRecruiter])
def ranked_candidates(request, job_id):
    """All applicants for a job, highest match first."""
    job = get_object_or_404(Job, pk=job_id, recruiter=request.user)
    apps = job.applications.select_related("candidate", "resume", "job").order_by(
        "-match_percentage", "created_at"
    )
    return Response(
        ApplicationSerializer(apps, many=True, context={"request": request}).data
    )


@api_view(["POST"])
@permission_classes([IsRecruiter])
def auto_select(request, job_id):
    """Select the candidate with the highest match percentage."""
    job = get_object_or_404(Job, pk=job_id, recruiter=request.user)
    best = select_best_candidate(job)
    if not best:
        return Response({"detail": "No applicants yet."}, status=status.HTTP_404_NOT_FOUND)
    return Response(ApplicationSerializer(best, context={"request": request}).data)


@api_view(["POST"])
@permission_classes([IsRecruiter])
def set_note(request, app_id):
    """Recruiter writes a short message to the candidate: body {"note": "..."}."""
    from django.utils import timezone

    app = get_object_or_404(Application, pk=app_id, job__recruiter=request.user)
    note = (request.data.get("note") or "").strip()[:500]
    app.recruiter_note = note
    app.note_updated_at = timezone.now() if note else None
    app.save(update_fields=["recruiter_note", "note_updated_at"])
    if note:
        notifications.recruiter_message(app)
    return Response(ApplicationSerializer(app, context={"request": request}).data)


@api_view(["POST"])
@permission_classes([IsRecruiter])
def set_status(request, app_id):
    """Recruiter picks a specific candidate: body {"status": selected|rejected|applied}."""
    app = get_object_or_404(Application, pk=app_id, job__recruiter=request.user)
    new = request.data.get("status")
    if new not in (Application.SELECTED, Application.REJECTED, Application.APPLIED):
        return Response({"detail": "Invalid status."}, status=400)
    set_application_status(app, new)
    return Response(ApplicationSerializer(app, context={"request": request}).data)


# ---------- Candidate ----------
class ApplyView(APIView):
    permission_classes = [IsCandidate]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, job_id):
        job = get_object_or_404(Job.active(), pk=job_id)
        if Application.objects.filter(candidate=request.user, job=job).exists():
            return Response({"detail": "You have already applied to this job."}, status=400)
        upload = request.FILES.get("resume")
        if upload:
            if not upload.name.lower().endswith(ALLOWED_EXTENSIONS):
                return Response(
                    {"detail": "Unsupported file type. Upload PDF, DOCX, TXT, PNG or JPG."},
                    status=400,
                )
            resume = Resume.objects.create(user=request.user, file=upload)
            try:
                parse_resume(resume)
            except UnreadableResume as e:
                resume.file.delete(save=False)
                resume.delete()
                return Response({"detail": str(e)}, status=400)
        else:  # reuse the latest uploaded resume
            resume = request.user.resumes.order_by("-uploaded_at").first()
            if not resume:
                return Response({"detail": "Upload a resume first."}, status=400)
        auto = str(request.data.get("auto_apply_related", "")).lower() in (
            "1",
            "true",
            "yes",
        )
        created = apply_to_job(request.user, job, resume, auto_apply_related=auto)
        return Response(
            ApplicationSerializer(created, many=True, context={"request": request}).data,
            status=201,
        )


class MyApplicationsView(generics.ListAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [IsCandidate]

    def get_queryset(self):
        return Application.objects.filter(candidate=self.request.user).select_related(
            "job", "resume", "candidate"
        )

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "request": self.request}


@api_view(["DELETE"])
@permission_classes([IsCandidate])
def withdraw_application(request, app_id):
    app = get_object_or_404(Application, pk=app_id, candidate=request.user)
    if app.status == Application.SELECTED:
        return Response({"detail": "You were selected for this job. Contact the recruiter instead of withdrawing."}, status=400)
    app.delete()
    return Response(status=204)


# ---------- Resumes (private files) ----------
@api_view(["GET"])
@permission_classes([IsCandidate])
def my_resumes(request):
    items = request.user.resumes.order_by("-uploaded_at")
    return Response(ResumeSerializer(items, many=True, context={"request": request}).data)


@api_view(["DELETE"])
@permission_classes([IsCandidate])
def delete_resume(request, resume_id):
    resume = get_object_or_404(Resume, pk=resume_id, user=request.user)
    n = resume.application_set.count()
    if n:
        return Response({"detail": f"This resume is used by {n} application(s). Withdraw them first, then delete it."}, status=400)
    resume.file.delete(save=False)
    resume.delete()
    return Response(status=204)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def resume_file(request, resume_id):
    """Resume files are NOT public. Only the owner, a recruiter who received it, or an admin can open one."""
    resume = get_object_or_404(Resume, pk=resume_id)
    u = request.user
    allowed = (
        resume.user_id == u.id
        or u.role == User.ADMIN
        or (u.role == User.RECRUITER and Application.objects.filter(resume=resume, job__recruiter=u).exists())
    )
    if not allowed or not resume.file:
        raise Http404()
    try:
        handle = resume.file.open("rb")
    except FileNotFoundError:
        raise Http404()
    return FileResponse(handle, as_attachment=False, filename=os.path.basename(resume.file.name))


# ---------- Admin ----------
@api_view(["GET"])
@permission_classes([IsAdminRole])
def admin_stats(request):
    return Response(
        {
            "users": User.objects.filter(role=User.CANDIDATE).count(),
            "recruiters": User.objects.filter(role=User.RECRUITER).count(),
            "jobs": Job.objects.count(),
            "applications": Application.objects.count(),
            "selected": Application.objects.filter(status=Application.SELECTED).count(),
            "pending_recruiters": User.objects.filter(role=User.RECRUITER, is_approved=False).count(),
        }
    )


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
    notifications.recruiter_decision(u)
    return Response({"id": u.id, "is_approved": u.is_approved})


@api_view(["GET"])
@permission_classes([IsAdminRole])
def admin_jobs(request):
    jobs = Job.objects.select_related("recruiter").order_by("-created_at")
    return Response(
        [
            {
                "id": j.id, "title": j.title, "company": j.company, "location": j.location,
                "recruiter": j.recruiter.username, "applicants": j.applications.count(),
                "is_open": j.is_open, "is_expired": j.is_expired, "expires_at": j.expires_at,
                "created_at": j.created_at,
            }
            for j in jobs
        ]
    )


@api_view(["DELETE"])
@permission_classes([IsAdminRole])
def admin_delete_job(request, job_id):
    get_object_or_404(Job, pk=job_id).delete()
    return Response(status=204)


# ---------- Recommendations ----------
@api_view(["POST"])
@permission_classes([IsCandidate])
@parser_classes([MultiPartParser, FormParser])
def upload_resume(request):
    """Upload + scan a resume without applying to a job."""
    upload = request.FILES.get("resume")
    if not upload:
        return Response({"detail": "Choose a resume file."}, status=400)
    if not upload.name.lower().endswith(ALLOWED_EXTENSIONS):
        return Response({"detail": "Unsupported file type. Upload PDF, DOCX, TXT, PNG or JPG."}, status=400)
    resume = Resume.objects.create(user=request.user, file=upload)
    try:
        parse_resume(resume)
    except UnreadableResume as e:
        resume.file.delete(save=False)
        resume.delete()
        return Response({"detail": str(e)}, status=400)
    data = ResumeSerializer(resume, context={"request": request}).data
    data["health"] = resume_health(resume.raw_text)
    return Response(data, status=201)


@api_view(["GET"])
@permission_classes([IsCandidate])
def recommendations(request):
    resume = request.user.resumes.order_by("-uploaded_at").first()
    if not resume:
        return Response({"has_resume": False})
    refresh_skills(resume)
    jobs = list(Job.active())
    data = build_recommendations(resume, jobs)
    data.update(
        has_resume=True,
        resume=ResumeSerializer(resume, context={"request": request}).data,
        jobs_count=len(jobs),
    )
    return Response(data)
