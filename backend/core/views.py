from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .matching import ALLOWED_EXTENSIONS, UnreadableResume, parse_resume
from .models import Application, Job, Resume, User
from .serializers import (
    ApplicationSerializer,
    JobSerializer,
    RegisterSerializer,
    ResumeSerializer,
)
from .services import apply_to_job, select_best_candidate


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
    """Candidates browse open jobs; `?q=` searches title/skills."""

    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Job.objects.filter(is_open=True).order_by("-created_at")
        q = self.request.query_params.get("q")
        if q:
            qs = qs.filter(title__icontains=q)
        return qs


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
    job = Job.objects.get(pk=job_id, recruiter=request.user)
    apps = job.applications.select_related("candidate").order_by("-match_percentage")
    return Response(ApplicationSerializer(apps, many=True).data)


@api_view(["POST"])
@permission_classes([IsRecruiter])
def auto_select(request, job_id):
    """Select the candidate with the highest match percentage."""
    job = Job.objects.get(pk=job_id, recruiter=request.user)
    best = select_best_candidate(job)
    if not best:
        return Response(
            {"detail": "No applicants yet."}, status=status.HTTP_404_NOT_FOUND
        )
    return Response(ApplicationSerializer(best).data)


# ---------- Candidate ----------
class ApplyView(APIView):
    permission_classes = [IsCandidate]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, job_id):
        job = Job.objects.get(pk=job_id, is_open=True)
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
        return Response(ApplicationSerializer(created, many=True).data, status=201)


class MyApplicationsView(generics.ListAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [IsCandidate]

    def get_queryset(self):
        return Application.objects.filter(candidate=self.request.user).select_related(
            "job"
        )


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
            }
            for u in self.get_queryset()
        ]
        return Response(data)


@api_view(["POST"])
@permission_classes([IsAdminRole])
def toggle_user(request, user_id):
    u = User.objects.get(pk=user_id)
    u.is_active = not u.is_active
    u.save(update_fields=["is_active"])
    return Response({"id": u.id, "is_active": u.is_active})
