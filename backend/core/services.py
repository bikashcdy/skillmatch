from django.db import transaction

from .matching import parse_resume, refresh_skills, score_match
from . import notifications
from .models import Application, Job

RELATED_THRESHOLD = 50.0  # minimum match % for a job to count as "related"
MAX_AUTO_APPLY = 5  # cap so one upload cannot spam dozens of jobs


@transaction.atomic
def apply_to_job(candidate, job, resume, auto_apply_related=False):
    """Apply to `job`. If the candidate opted in, also apply to related open jobs."""
    if not resume.extracted_skills and not resume.raw_text:
        parse_resume(resume)
    else:
        refresh_skills(resume)

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
            Job.active()
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
    if created:
        transaction.on_commit(lambda apps=list(created): notifications.strong_matches(apps))
    return created


def set_application_status(application, new_status):
    """Change an application's status. Only one candidate can be selected per job."""
    with transaction.atomic():
        if new_status == Application.SELECTED:
            application.job.applications.filter(status=Application.SELECTED).exclude(
                pk=application.pk
            ).update(status=Application.APPLIED)
        changed = application.status != new_status
        application.status = new_status
        application.save(update_fields=["status"])
    if changed and new_status in (Application.SELECTED, Application.REJECTED):
        notifications.application_decision(application)
    return application


def select_best_candidate(job):
    """Select the highest-scoring non-rejected application (previous pick is reset)."""
    best = (
        job.applications.exclude(status=Application.REJECTED)
        .order_by("-match_percentage", "created_at")
        .first()
    )
    if best:
        set_application_status(best, Application.SELECTED)
    return best
