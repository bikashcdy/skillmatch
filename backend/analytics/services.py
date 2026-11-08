"""Platform statistics and skill-demand reports."""

from collections import Counter

from accounts.models import User
from applications.models import Application
from jobs.models import Job
from resumes.models import Resume


def overview():
    return {
        "users": User.objects.filter(role=User.CANDIDATE).count(),
        "recruiters": User.objects.filter(role=User.RECRUITER).count(),
        "jobs": Job.objects.count(),
        "applications": Application.objects.count(),
        "selected": Application.objects.filter(status=Application.SELECTED).count(),
        "pending_recruiters": User.objects.filter(role=User.RECRUITER, is_approved=False).count(),
    }


def skill_demand(limit=12):
    """Which skills do open jobs ask for, how many candidates have them, and where do candidates fall short?"""
    must, nice = Counter(), Counter()
    jobs = list(Job.active())
    for job in jobs:
        must.update(job.required_skills or [])
        nice.update(job.nice_to_have_skills or [])
    supply = Counter()
    seen = set()
    for resume in Resume.objects.filter(confirmed=True).order_by("-uploaded_at"):
        if resume.user_id in seen:  # only each candidate's latest confirmed resume counts
            continue
        seen.add(resume.user_id)
        supply.update(set(resume.extracted_skills or []))
    candidates = len(seen)
    demand = [
        {
            "skill": skill, "jobs": must[skill] + nice[skill], "must_have_jobs": must[skill],
            "candidates": supply[skill],
            "shortage": max(must[skill] + nice[skill] - supply[skill], 0),
        }
        for skill in set(must) | set(nice)
    ]
    demand.sort(key=lambda d: (-d["jobs"], d["skill"]))

    apps = list(Application.objects.exclude(status=Application.REJECTED).values(
        "match_percentage", "knockout", "missing_skills"))
    buckets = {"0-39": 0, "40-59": 0, "60-74": 0, "75-100": 0}
    missing = Counter()
    for a in apps:
        p = a["match_percentage"]
        buckets["75-100" if p >= 75 else "60-74" if p >= 60 else "40-59" if p >= 40 else "0-39"] += 1
        missing.update(a["missing_skills"] or [])
    return {
        "open_jobs": len(jobs),
        "candidates": candidates,
        "top_demand": demand[:limit],
        "most_missing": [{"skill": s, "times": n} for s, n in missing.most_common(limit)],
        "match_distribution": buckets,
        "applications": len(apps),
        "knockout_rate": round(100 * sum(1 for a in apps if a["knockout"]) / len(apps), 1) if apps else 0,
        "average_match": round(sum(a["match_percentage"] for a in apps) / len(apps), 1) if apps else 0,
    }
