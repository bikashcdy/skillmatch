"""Candidate profile: job preferences and the skills confirmed on the latest resume."""

from jobs.models import Job
from jobs.validators import job_location_errors


def update_preferences(user, data):
    """Validate and save the optional job preferences. Returns a dict of errors, or None when saved."""
    loc = " ".join((data.get("preferred_location", user.preferred_location) or "").split())
    job_type = (data.get("preferred_job_type", user.preferred_job_type) or "").strip()
    errors = {}
    if loc and job_location_errors(loc):
        errors["preferred_location"] = job_location_errors(loc)
    if job_type and job_type not in dict(Job.JOB_TYPES):
        errors["preferred_job_type"] = ["Choose a valid job type."]
    if errors:
        return errors
    user.preferred_location, user.preferred_job_type = loc, job_type
    user.save(update_fields=["preferred_location", "preferred_job_type"])
    return None


def profile_summary(user):
    resume = user.resumes.filter(confirmed=True).order_by("-uploaded_at").first()
    return {
        "preferred_location": user.preferred_location,
        "preferred_job_type": user.preferred_job_type,
        "has_resume": bool(resume),
        "skills": resume.extracted_skills if resume else [],
        "experience_years": resume.experience_years if resume else 0,
        "education_level": resume.education_level if resume else "",
        "projects": resume.projects if resume else [],
        "certifications": resume.certifications if resume else [],
        "completeness": _completeness(user, resume),
    }


def _completeness(user, resume):
    """Share of profile parts that are filled in (0-100): resume, skills, experience, education, preferences."""
    parts = [
        bool(resume),
        bool(resume and resume.extracted_skills),
        bool(resume and resume.experience_years),
        bool(resume and resume.education_level not in ("", "none")),
        bool(user.preferred_location or user.preferred_job_type),
    ]
    return round(100 * sum(parts) / len(parts))
