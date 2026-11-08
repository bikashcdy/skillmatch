"""Skill gap: the share of the job's skills the candidate has not got at all."""


def skill_gap_percentage(missing, total_skills):
    """Gap % = missing skills / total required skills x 100. Partial skills are not counted as missing."""
    if not total_skills:
        return 0.0
    return round(100.0 * len(missing) / total_skills, 1)
