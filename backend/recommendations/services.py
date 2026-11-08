"""Career recommendations: which skills to learn to raise the candidate's match %."""

from dataclasses import replace

from matching.engine import generate_learning_path
from matching.engine.skill_data import EDUCATION_LEVELS, EDUCATION_NAMES, PREREQUISITES
from matching.services import profile_for, scorer_for
from resumes.extractors import candidate_text
from resumes.health import resume_health

from .data import GENERAL_IDEAS, resources_for


def build_recommendations(resume, jobs):  # noqa: C901
    """Return skill gaps (ranked by impact), best-fit jobs, a learning path and experience/education tips."""
    have = set(resume.extracted_skills)
    scorer, profile = scorer_for(jobs), profile_for(resume)
    baseline = {j.id: scorer.score(profile, j) for j in jobs}

    gaps = {}
    for j in jobs:  # missing skills and skills with only half credit are both worth learning
        for s in baseline[j.id]["missing_skills"] + baseline[j.id]["partial_skills"]:
            gaps.setdefault(s, []).append(j)

    skill_gaps = []
    for skill, needing in gaps.items():
        with_skill = replace(profile, skills=sorted(set(profile.skills) | {skill}))
        gains, unlocks = [], []
        for j in needing:
            new = scorer.score(with_skill, j)["match_percentage"]
            old = baseline[j.id]["match_percentage"]
            gains.append(new - old)
            if old < 75 <= new:
                unlocks.append(j.title)
        why, weeks, links = resources_for(skill)
        avg = sum(gains) / len(gains)
        skill_gaps.append({
            "skill": skill,
            "why": why,
            "jobs_needing": len(needing),
            "avg_gain": round(avg, 1),
            "unlocks": unlocks[:3],
            "weeks": weeks,
            "priority_score": round(avg * len(needing), 1),
            "resources": links,
            "job_titles": [j.title for j in needing][:4],
        })
    skill_gaps.sort(key=lambda g: (-g["priority_score"], g["skill"]))
    skill_gaps = skill_gaps[:8]
    for i, g in enumerate(skill_gaps):
        g["rank"] = i + 1

    # What if the top 3 skills were learned? (the best 6 jobs come from a min-heap Top-K)
    top3 = [g["skill"] for g in skill_gaps[:3]]
    future = replace(profile, skills=sorted(set(profile.skills) | set(top3)))
    best = []
    for j, now in scorer.top_k(profile, jobs, k=6):
        best.append({
            "id": j.id, "title": j.title, "company": j.company, "location": j.location,
            "match": now["match_percentage"], "match_after": scorer.score(future, j)["match_percentage"],
            "matched_skills": now["matched_skills"], "partial_skills": now["partial_skills"],
            "missing_skills": now["missing_skills"], "knockout": now["knockout"],
            "missing_must_have": now["missing_must_have"], "skill_gap": now["skill_gap"],
        })

    # Learning path: the skills to learn, with prerequisites first (topological order)
    gap_names = [g["skill"] for g in skill_gaps]
    path = []
    for skill in generate_learning_path(gap_names, have):
        _, weeks, _ = resources_for(skill)
        path.append({
            "skill": skill, "weeks": weeks, "is_gap": skill in gap_names,
            "needed_for": sorted(g for g in gap_names if skill in PREREQUISITES.get(g, [])),
        })

    tips = []
    max_exp = max((j.min_experience_years for j in jobs), default=0)
    if resume.experience_years < max_exp:
        tips.append({
            "area": "Experience",
            "text": (f"Your resume shows {resume.experience_years:g} year(s); some jobs ask for up to {max_exp:g}. "
                     "If you have worked, interned or freelanced, write it as '2 years' or '6 months' so the scanner can read it. "
                     "Otherwise build real projects and look for internships."),
        })
    top_edu = max((EDUCATION_LEVELS.get((j.required_education or "none").lower(), 0) for j in jobs), default=0)
    mine = EDUCATION_LEVELS.get(resume.education_level or "none", 0)
    if mine < top_edu:
        tips.append({
            "area": "Education",
            "text": (f"Some jobs prefer a {EDUCATION_NAMES[top_edu]} qualification and your resume shows '{resume.education_level}'. "
                     "Make sure your degree (BCA, BSc CSIT, +2, diploma) is written clearly. Certificates help your profile, "
                     "but the match score only counts the degree level."),
        })
    if len(have) < 5:
        tips.append({"area": "Resume", "text": "Only a few skills were detected. List your tools and technologies in a Skills section using common names (Python, React, SQL, Git)."})

    avg_now = round(sum(b["match"] for b in best[:5]) / max(len(best[:5]), 1), 1)
    avg_after = round(sum(b["match_after"] for b in best[:5]) / max(len(best[:5]), 1), 1)
    return {
        "health": resume_health(resume.raw_text or candidate_text(resume)),
        "skills_have": sorted(have),
        "skill_gaps": skill_gaps,
        "learning_path": path,
        "best_jobs": best,
        "tips": tips,
        "ideas": GENERAL_IDEAS,
        "focus": top3,
        "avg_now": avg_now,
        "avg_after": avg_after,
        "weeks_total": sum(g["weeks"] for g in skill_gaps[:3]),
    }
