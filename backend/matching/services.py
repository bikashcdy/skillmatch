"""Glue between the Django models and the independent matching engine (core/engine/)."""

from .engine import CandidateProfile, MatchEngine, Recommender, TextScorer, job_text
from .engine.match_engine import DEFAULT_WEIGHTS
from resumes.extractors import candidate_text
from jobs.models import Job

from .models import WeightConfig

# model fields stored on an Application (the engine result has a few extra keys for the UI)
APPLICATION_FIELDS = (
    "match_percentage", "skill_score", "text_score", "experience_score", "education_score",
    "preference_score", "matched_skills", "partial_skills", "missing_skills", "knockout", "skill_gap",
)


def application_fields(result):
    return {k: result[k] for k in APPLICATION_FIELDS}


def active_weights():
    """The weights an admin activated after tuning, or the defaults from the algorithm document."""
    config = WeightConfig.objects.filter(is_active=True).first()
    return (dict(config.weights), config.version) if config else (dict(DEFAULT_WEIGHTS), 0)


def profile_for(resume, extra_skills=()):
    user = resume.user
    return CandidateProfile(
        skills=sorted(set(resume.extracted_skills or []) | set(extra_skills)),
        experience_years=resume.experience_years or 0,
        education_level=resume.education_level or "",
        text=candidate_text(resume),
        preferred_location=getattr(user, "preferred_location", "") or "",
        preferred_job_type=getattr(user, "preferred_job_type", "") or "",
    )


def scorer_for(corpus_jobs=None, scorer=None, weights=None):
    """A Recommender (scorer with a cache). Build it once per request and reuse it for every job.

    The IDF statistics come from the descriptions of all active jobs, so words every job uses
    ("developer", "team") count for less than distinctive ones.
    """
    if scorer is not None:
        return scorer
    jobs = list(corpus_jobs) if corpus_jobs is not None else list(Job.active())
    if weights is None:
        weights, version = active_weights()
    else:
        version = -1
    texts = [job_text(j) for j in jobs]
    engine = MatchEngine(weights=weights, text_scorer=TextScorer(texts))
    return Recommender(engine, weights_version=version, corpus_signature=hash(tuple(sorted(hash(t) for t in texts))))
