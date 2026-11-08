from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsCandidate, IsRecruiter
from jobs.models import Job
from resumes.models import Resume

from . import notifications
from .models import Application
from .serializers import ApplicationSerializer
from .services import apply_to_job, select_best_candidate, set_application_status


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


class ApplyView(APIView):
    permission_classes = [IsCandidate]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request, job_id):
        job = get_object_or_404(Job.active(), pk=job_id)
        if Application.objects.filter(candidate=request.user, job=job).exists():
            return Response({"detail": "You have already applied to this job."}, status=400)
        if request.FILES.get("resume"):
            return Response(
                {"detail": "Upload your resume first, check the scanned details, then apply."}, status=400
            )
        resume_id = request.data.get("resume_id")
        if resume_id:
            resume = get_object_or_404(Resume, pk=resume_id, user=request.user)
        else:  # reuse the latest confirmed resume
            resume = request.user.resumes.filter(confirmed=True).order_by("-uploaded_at").first()
            if not resume:
                return Response({"detail": "Upload a resume first."}, status=400)
        if not resume.confirmed:
            return Response({"detail": "Please check and confirm your resume details before applying."}, status=400)
        auto = str(request.data.get("auto_apply_related", "")).lower() in ("1", "true", "yes")
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
