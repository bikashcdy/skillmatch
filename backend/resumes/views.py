import os

from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from accounts.models import User
from accounts.permissions import IsCandidate
from applications.models import Application
from matching.engine import extract_skills

from .health import resume_health
from .models import Resume
from .ocr import ocr_status
from .parser import ALLOWED_EXTENSIONS, UnreadableResume
from .serializers import ResumeSerializer
from .services import parse_resume, resume_payload


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


def resume_response(request, resume, status_code=200):
    data = ResumeSerializer(resume, context={"request": request}).data
    data["health"] = resume_health(resume.raw_text)
    return Response(data, status=status_code)


@api_view(["POST"])
@permission_classes([IsCandidate])
@parser_classes([MultiPartParser, FormParser])
def upload_resume(request):
    """Upload + scan a resume. The result must be checked and confirmed by the candidate."""
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
        return Response({"detail": str(e), "manual_entry": True}, status=400)
    return resume_response(request, resume, 201)


@api_view(["POST"])
@permission_classes([IsCandidate])
def confirm_resume(request, resume_id):
    """The candidate checked (and maybe corrected) the scanned details. Only then can the resume be used."""
    resume = get_object_or_404(Resume, pk=resume_id, user=request.user)
    values, errors = resume_payload(request.data)
    if errors:
        return Response(errors, status=400)
    scanned = set(extract_skills(resume.raw_text)) if resume.raw_text else None
    for field, value in values.items():
        setattr(resume, field, value)
    resume.skills_edited = scanned is None or set(values["extracted_skills"]) != scanned
    resume.confirmed, resume.confirmed_at = True, timezone.now()
    resume.save()
    return resume_response(request, resume)


@api_view(["POST"])
@permission_classes([IsCandidate])
def manual_resume(request):
    """Fallback when a file cannot be read: the candidate types their details in."""
    values, errors = resume_payload(request.data)
    if errors:
        return Response(errors, status=400)
    resume = Resume.objects.create(
        user=request.user, skills_edited=True, confirmed=True, confirmed_at=timezone.now(), **values
    )
    return resume_response(request, resume, 201)


@api_view(["GET"])
@permission_classes([IsCandidate])
def ocr_state(request):
    """Can this server read photos and scanned resumes? The upload screens show this to candidates."""
    return Response(ocr_status())
