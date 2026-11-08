"""Weighted skill coverage: must-have skills count double, related skills count half."""

from .skill_data import SKILL_GROUPS
from .skill_normalizer import normalize_skill

MUST_IMPORTANCE = 2
NICE_IMPORTANCE = 1
EXACT, RELATED, MISSING = 1.0, 0.5, 0.0


def related_skill(skill, candidate_skills):
    """Return a candidate skill in the same skill group as `skill`, or None."""
    for members in SKILL_GROUPS.values():
        if skill in members:
            for other in members:
                if other != skill and other in candidate_skills:
                    return other
    return None


def score_skills(candidate_skills, must_have, nice_to_have=()):
    """S_skill = sum(importance * matching value) / sum(importance).

    Returns the score (0..1) and the matched / partial / missing lists.
    knockout is True when a must-have skill is completely missing.
    """
    have = {normalize_skill(s) for s in candidate_skills}
    must = sorted({normalize_skill(s) for s in must_have if s})
    nice = sorted({normalize_skill(s) for s in nice_to_have if s} - set(must))

    weighted, total = 0.0, 0
    matched, partial, missing, related_to = [], [], [], {}
    missing_must = []
    for importance, skills in ((MUST_IMPORTANCE, must), (NICE_IMPORTANCE, nice)):
        for skill in skills:
            if skill in have:
                value = EXACT
                matched.append(skill)
            else:
                other = related_skill(skill, have)
                if other:
                    value = RELATED
                    partial.append(skill)
                    related_to[skill] = other
                else:
                    value = MISSING
                    missing.append(skill)
                    if importance == MUST_IMPORTANCE:
                        missing_must.append(skill)
            weighted += importance * value
            total += importance

    return {
        "score": weighted / total if total else 1.0,
        "matched": sorted(matched),
        "partial": sorted(partial),
        "missing": sorted(missing),
        "missing_must_have": sorted(missing_must),
        "related_to": related_to,
        "knockout": bool(missing_must),
        "total_skills": len(must) + len(nice),
    }
