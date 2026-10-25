from django.db import transaction

from .matching import parse_resume, score_match
from .models import Application, Job

RELATED_THRESHOLD = 50.0  # minimum match % for a job to count as "related"
MAX_AUTO_APPLY = 5  # cap so one upload cannot spam dozens of jobs


@transaction.atomic
def apply_to_job(candidate, job, resume, auto_apply_related=False):
    """Apply to `job`. If the candidate opted in, also apply to related open jobs."""
    if not resume.extracted_skills and not resume.raw_text:
        parse_resume(resume)

    created = []
    app, was_new = Application.objects.get_or_create(
        candidate=candidate,
        job=job,
        defaults={
            "resume": resume,
            "status": Application.APPLIED,
            **score_match(resume, job),
        },
    )
    if was_new:
        created.append(app)

    if auto_apply_related:
        others = (
            Job.objects.filter(is_open=True)
            .exclude(pk=job.pk)
            .exclude(applications__candidate=candidate)
        )
        scored = []
        for other in others:
            result = score_match(resume, other)
            if result["match_percentage"] >= RELATED_THRESHOLD:
                scored.append((other, result))
        scored.sort(key=lambda x: x[1]["match_percentage"], reverse=True)
        for other, result in scored[:MAX_AUTO_APPLY]:
            created.append(
                Application.objects.create(
                    candidate=candidate,
                    job=other,
                    resume=resume,
                    status=Application.AUTO,
                    **result
                )
            )
    return created


def select_best_candidate(job):
    """Mark the highest-scoring application as selected, others stay as applied."""
    apps = job.applications.exclude(status=Application.REJECTED).order_by(
        "-match_percentage"
    )
    best = apps.first()
    if best:
        best.status = Application.SELECTED
        best.save(update_fields=["status"])
    return best
