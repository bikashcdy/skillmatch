from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.permissions import IsAdminRole, IsCandidate
from jobs.models import Job
from resumes.models import Resume

from .models import RelevanceRating, WeightConfig
from .services import profile_for, scorer_for


def _rating_row(r):
    return {
        "id": r.id, "resume": r.resume_id, "candidate": r.resume.user.username, "job": r.job_id,
        "job_title": r.job.title, "rating": r.rating, "split": r.split,
    }


def _config_row(c):
    return {
        "id": c.id, "version": c.version, "weights": c.weights, "tuning_ndcg": c.tuning_ndcg,
        "test_ndcg": c.test_ndcg, "is_active": c.is_active, "note": c.note, "created_at": c.created_at,
    }


@api_view(["GET"])
@permission_classes([IsAdminRole])
def admin_weights(request):
    from .engine.match_engine import DEFAULT_WEIGHTS
    from .evaluation import evaluate
    from .services import active_weights

    weights, version = active_weights()
    ratings = RelevanceRating.objects.select_related("resume__user", "job").order_by("-created_at")
    return Response({
        "defaults": DEFAULT_WEIGHTS,
        "active": weights,
        "active_version": version,
        "configs": [_config_row(c) for c in WeightConfig.objects.all()],
        "ratings": [_rating_row(r) for r in ratings],
        "counts": {
            "tune": ratings.filter(split="tune").count(),
            "test": ratings.filter(split="test").count(),
        },
        "evaluation": evaluate(scorer_for(), None) if ratings.exists() else None,
        "resumes": [
            {"id": r.id, "label": f"{r.user.username} (resume #{r.id})"}
            for r in Resume.objects.select_related("user").order_by("-uploaded_at")[:200]
        ],
        "jobs": [{"id": j.id, "label": f"{j.title} @ {j.company}"} for j in Job.objects.order_by("-created_at")[:200]],
    })


@api_view(["POST"])
@permission_classes([IsAdminRole])
def admin_rate(request):
    try:
        rating = int(request.data.get("rating"))
    except (TypeError, ValueError):
        return Response({"detail": "Rating must be a number from 0 to 3."}, status=400)
    split = request.data.get("split") or "tune"
    if not 0 <= rating <= 3 or split not in ("tune", "test"):
        return Response({"detail": "Rating must be 0-3 and split must be tune or test."}, status=400)
    resume = get_object_or_404(Resume, pk=request.data.get("resume"))
    job = get_object_or_404(Job, pk=request.data.get("job"))
    RelevanceRating.objects.update_or_create(resume=resume, job=job, defaults={"rating": rating, "split": split})
    return Response({"ok": True}, status=201)


@api_view(["POST"])
@permission_classes([IsAdminRole])
def admin_import_decisions(request):
    """Create ratings from real recruiter decisions (selected / rejected) so tuning has data to learn from."""
    from .evaluation import import_recruiter_decisions

    return Response({"created": import_recruiter_decisions()}, status=201)


@api_view(["DELETE"])
@permission_classes([IsAdminRole])
def admin_delete_rating(request, rating_id):
    get_object_or_404(RelevanceRating, pk=rating_id).delete()
    return Response(status=204)


@api_view(["POST"])
@permission_classes([IsAdminRole])
def admin_tune(request):
    """Grid-search the five weights (steps of 0.05) for the best NDCG@5 on the tuning ratings."""
    from .engine import tune_weights
    from .evaluation import dataset_warnings, rating_groups

    scorer = scorer_for(weights={})  # default weights; only the component scores are used
    tuning = rating_groups(scorer, "tune")
    if not tuning:
        return Response(
            {"detail": "Rate at least 2 jobs for 1 resume (or 2 candidates for 1 job) in the tuning set first."}, status=400
        )
    testing = rating_groups(scorer, "test")
    result = tune_weights(tuning, testing or None)
    result["warnings"] = dataset_warnings(tuning, testing)
    version = (WeightConfig.objects.order_by("-version").values_list("version", flat=True).first() or 0) + 1
    config = WeightConfig.objects.create(
        version=version, weights=result["weights"], tuning_ndcg=result["tuning_ndcg"], test_ndcg=result["test_ndcg"],
        note=f"Grid search, {result['combinations_tested']} combinations",
    )
    result["config"] = _config_row(config)
    return Response(result, status=201)


@api_view(["POST"])
@permission_classes([IsAdminRole])
def admin_activate_weights(request, config_id=None):
    """Make a tuned configuration live (config_id), or go back to the default weights (no id)."""
    from .engine.recommender import clear_cache

    WeightConfig.objects.update(is_active=False)
    if config_id is not None:
        config = get_object_or_404(WeightConfig, pk=config_id)
        config.is_active = True
        config.save(update_fields=["is_active"])
    clear_cache()
    return Response({"ok": True})


@api_view(["GET"])
@permission_classes([IsCandidate])
def job_match(request, job_id):
    """How well does the candidate's confirmed resume match one job? Returns the full score breakdown."""
    job = get_object_or_404(Job.active(), pk=job_id)
    resume = request.user.resumes.filter(confirmed=True).order_by("-uploaded_at").first()
    if not resume:
        return Response({"detail": "Upload and confirm a resume first."}, status=400)
    return Response(scorer_for().score(profile_for(resume), job))
