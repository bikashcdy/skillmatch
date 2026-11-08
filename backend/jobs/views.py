import datetime

from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from accounts.models import User
from accounts.permissions import IsAdminRole, IsRecruiter
from applications.models import Application
from matching.engine.skill_data import SKILLS
from matching.engine import normalize_skill
from matching.services import profile_for, scorer_for
from resumes.extractors import refresh_skills

from .constants import NEPAL_CITIES
from .models import Job, nepal_today
from .serializers import JobSerializer


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
                or canon in (j.required_skills + j.nice_to_have_skills)
                or any(q in sk for sk in (j.required_skills + j.nice_to_have_skills))
            ]
        skill = (p.get("skill") or "").strip()
        if skill:
            canon = normalize_skill(skill)
            jobs = [j for j in jobs if canon in (j.required_skills + j.nice_to_have_skills)]
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
            resume = u.resumes.filter(confirmed=True).order_by("-uploaded_at").first()
            if resume:
                refresh_skills(resume)
                active = list(Job.active())
                scorer, profile = scorer_for(active), profile_for(resume)
                ctx["match_map"] = {j.id: scorer.score(profile, j)["match_percentage"] for j in active}
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
            resume = u.resumes.filter(confirmed=True).order_by("-uploaded_at").first()
            if resume:
                refresh_skills(resume)
                detail = scorer_for().score(profile_for(resume), job)
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
