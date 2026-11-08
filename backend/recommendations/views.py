from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.permissions import IsCandidate
from jobs.models import Job
from matching.engine import generate_learning_path
from matching.engine.whatif import simulate
from matching.engine import normalize_skill
from matching.services import profile_for, scorer_for
from resumes.extractors import refresh_skills
from resumes.serializers import ResumeSerializer

from .services import build_recommendations


@api_view(["GET"])
@permission_classes([IsCandidate])
def recommendations(request):
    resume = request.user.resumes.filter(confirmed=True).order_by("-uploaded_at").first()
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


@api_view(["POST"])
@permission_classes([IsCandidate])
def what_if(request):
    """Simulate learning extra skills. The candidate's real profile is never changed."""
    resume = request.user.resumes.filter(confirmed=True).order_by("-uploaded_at").first()
    if not resume:
        return Response({"detail": "Upload and confirm a resume first."}, status=400)
    raw = request.data.get("skills")
    if not isinstance(raw, list) or not raw or len(raw) > 10:
        return Response({"detail": "Choose between 1 and 10 skills to simulate."}, status=400)
    skills = sorted({normalize_skill(str(x)) for x in raw if str(x).strip()})
    jobs = list(Job.active())
    scorer, profile = scorer_for(jobs), profile_for(resume)
    rows = simulate(profile, jobs, skills, lambda p, j: scorer.score(p, j))
    top = sorted(rows, key=lambda r: -r["before"])[:5]
    avg = lambda key: round(sum(r[key] for r in top) / len(top), 1) if top else 0  # noqa: E731
    return Response({
        "skills": skills,
        "jobs": rows[:10],
        "avg_before": avg("before"),
        "avg_after": avg("after"),
        "crossing": [r["title"] for r in rows if r["crosses_threshold"]],
        "learning_path": generate_learning_path(skills, profile.skills),
    })
