from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .matching import (
    ALLOWED_EXTENSIONS,
    UnreadableResume,
    normalize_skill,
    parse_resume,
    score_match,
)
from .models import Application, Job, Resume, User
from .serializers import (
    ApplicationSerializer,
    JobSerializer,
    RegisterSerializer,
    ResumeSerializer,
)
from .recommendations import NEPAL_CITIES, build_recommendations
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


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def me(request):
    u = request.user
    return Response(
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "company_name": u.company_name,
        }
    )


# ---------- Jobs ----------
class JobListView(generics.ListAPIView):
    """Open jobs. Filters: ?q= (title/company/skill), ?location=, ?skill=."""

    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        p = self.request.query_params
        qs = Job.objects.filter(is_open=True).order_by("-created_at")
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
        return jobs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        u = self.request.user
        if u.role == User.CANDIDATE:
            ctx["my_apps"] = {a.job_id: a for a in Application.objects.filter(candidate=u)}
            resume = u.resumes.order_by("-uploaded_at").first()
            if resume:
                ctx["match_map"] = {
                    j.id: score_match(resume, j)["match_percentage"]
                    for j in Job.objects.filter(is_open=True)
                }
        return ctx


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def job_meta(request):
    """Data for the search bar: locations, trending skills and headline numbers."""
    jobs = list(Job.objects.filter(is_open=True))
    skills, locations = {}, {}
    for j in jobs:
        for sk in j.required_skills:
            skills[sk] = skills.get(sk, 0) + 1
        loc = (j.location or "").strip()
        if loc:
            locations[loc] = locations.get(loc, 0) + 1
    ranked = sorted(skills.items(), key=lambda x: (-x[1], x[0]))
    return Response(
        {
            "skills": [{"name": n, "count": c} for n, c in ranked],
            "locations": sorted(locations),
            "cities": [{"name": c, "count": locations.get(c, 0)} for c in NEPAL_CITIES],
            "stats": {
                "jobs": len(jobs),
                "companies": len({j.company for j in jobs}),
                "candidates": User.objects.filter(role=User.CANDIDATE, is_active=True).count(),
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
        serializer.save(recruiter=u, company=u.company_name or u.username)


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
        job = get_object_or_404(Job, pk=job_id, is_open=True)
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
    return Response(ResumeSerializer(resume, context={"request": request}).data, status=201)


@api_view(["GET"])
@permission_classes([IsCandidate])
def recommendations(request):
    resume = request.user.resumes.order_by("-uploaded_at").first()
    if not resume:
        return Response({"has_resume": False})
    jobs = list(Job.objects.filter(is_open=True))
    data = build_recommendations(resume, jobs)
    data.update(
        has_resume=True,
        resume=ResumeSerializer(resume, context={"request": request}).data,
        jobs_count=len(jobs),
    )
    return Response(data)
