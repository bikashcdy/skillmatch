"""What-if simulation: how would learning extra skills change the match scores?"""

import copy

from .match_engine import CandidateProfile

THRESHOLD = 75.0  # a job "crosses" the recommendation threshold when it reaches this score


def simulate(candidate, jobs, new_skills, scorer):
    """`scorer(candidate, job)` returns an engine result. The real profile is never modified."""
    temp = copy.deepcopy(candidate)  # temporary copy
    temp.skills = sorted(set(temp.skills) | set(new_skills))
    rows = []
    for job in jobs:
        before = scorer(candidate, job)["match_percentage"]
        after = scorer(temp, job)["match_percentage"]
        rows.append({
            "id": job.pk, "title": job.title, "company": job.company,
            "before": before, "after": after, "change": round(after - before, 1),
            "crosses_threshold": before < THRESHOLD <= after,
        })
    rows.sort(key=lambda r: (-r["change"], -r["after"]))
    return rows
