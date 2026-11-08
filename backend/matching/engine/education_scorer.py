"""Education score: S_edu = min(candidate level / required level, 1)."""

from .skill_data import EDUCATION_LEVELS


def education_level(name):
    return EDUCATION_LEVELS.get((name or "none").strip().lower(), 0)


def score_education(candidate_education, required_education):
    needed = education_level(required_education)
    if needed == 0:
        return 1.0
    return min(education_level(candidate_education) / needed, 1.0)
