"""Evaluate and tune the matching weights against manually rated resume/job pairs."""

from collections import defaultdict

from .engine import cohens_kappa, ndcg_at_k, precision_at_k, spearman
from .engine.match_engine import combine
from .services import profile_for
from .models import RelevanceRating


def rating_groups(scorer, split=None):
    """Ranking queries built from the rated pairs: {query: [(component scores, knockout, rating), ...]}.

    There are two kinds of query: "which jobs fit this resume?" (key r<id>) and the recruiter's
    "which candidates fit this job?" (key j<id>). A pair can appear in both.
    """
    qs = RelevanceRating.objects.select_related("resume", "resume__user", "job")
    if split:
        qs = qs.filter(split=split)
    groups, profiles = defaultdict(list), {}
    for r in qs:
        profile = profiles.setdefault(r.resume_id, profile_for(r.resume))
        values, skills, _ = scorer.engine.components(profile, r.job)
        item = (values, skills["knockout"], r.rating)
        groups[f"r{r.resume_id}"].append(item)
        groups[f"j{r.job_id}"].append(item)
    return {k: v for k, v in groups.items() if len(v) >= 2}  # a ranking needs at least 2 items


def _bucket(score):
    return 3 if score >= 75 else 2 if score >= 60 else 1 if score >= 40 else 0


def evaluate(scorer, split=None, k=5):
    """Ranking quality of the engine's current weights: Precision@k, NDCG@k, Spearman, Cohen's kappa."""
    groups = rating_groups(scorer, split)
    p_at_k, ndcgs, rhos, engine_labels, manual_labels = [], [], [], [], []
    seen = set()  # a pair that sits in two queries must only count once for the agreement score
    for items in groups.values():
        scored = [(combine(c, scorer.engine.weights, ko)[0], rating) for c, ko, rating in items]
        ranked = sorted(scored, key=lambda x: -x[0])
        relevances = [r for _, r in ranked]
        p_at_k.append(precision_at_k(relevances, k))
        ndcgs.append(ndcg_at_k(relevances, k))
        if len(scored) >= 3:
            rhos.append(spearman([s for s, _ in scored], [r for _, r in scored]))
        for item, (score, rating) in zip(items, scored):
            if id(item) not in seen:
                seen.add(id(item))
                engine_labels.append(_bucket(score))
                manual_labels.append(rating)
    mean = lambda xs: round(sum(xs) / len(xs), 4) if xs else None  # noqa: E731
    return {
        "queries": len(groups),
        "pairs": len(manual_labels),
        f"precision_at_{k}": mean(p_at_k),
        f"ndcg_at_{k}": mean(ndcgs),
        "spearman": mean(rhos),
        "cohens_kappa": round(cohens_kappa(engine_labels, manual_labels), 4) if manual_labels else None,
    }


SMALL_DATASET = 30  # below this many rated pairs a tuned result is probably just noise


def dataset_warnings(tuning, testing):
    pairs = len({id(i) for items in tuning.values() for i in items})
    warnings = []
    if pairs < SMALL_DATASET:
        warnings.append(f"Only {pairs} rated pairs in the tuning set. Rate at least {SMALL_DATASET} for a reliable result.")
    if not testing:
        warnings.append("There is no test set, so the result is not checked on unseen data. Rate some pairs as 'test'.")
    return warnings


def import_recruiter_decisions():
    """Turn real recruiter decisions into relevance ratings: selected = 3 (perfect), rejected = 0.

    Existing ratings (for example manual ones) are never overwritten. The split is fixed by the resume id
    (every 5th resume is held back for testing) so the same pair always lands in the same set.
    Note: recruiters see the engine's ranking, so these labels are a starting point, not a gold standard.
    """
    from .models import Application

    created = 0
    for app in Application.objects.filter(status__in=[Application.SELECTED, Application.REJECTED]).select_related("resume"):
        if app.resume.ratings.filter(job=app.job).exists():
            continue
        RelevanceRating.objects.create(
            resume=app.resume, job=app.job, rating=3 if app.status == Application.SELECTED else 0,
            split=RelevanceRating.TEST if app.resume_id % 5 == 0 else RelevanceRating.TUNE,
        )
        created += 1
    return created
