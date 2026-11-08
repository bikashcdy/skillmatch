"""Preference score: satisfied preferences / preferences the candidate actually gave."""


def _same_place(wanted, actual):
    w, a = (wanted or "").strip().lower(), (actual or "").strip().lower()
    return bool(w and a and (w in a or a in w))


def score_preferences(preferred_location, preferred_job_type, job_location, job_type):
    """Returns (score 0..1, satisfied, total). Score is None when no preference was given."""
    total = satisfied = 0
    if (preferred_location or "").strip():
        total += 1
        satisfied += _same_place(preferred_location, job_location)
    if (preferred_job_type or "").strip():
        total += 1
        satisfied += preferred_job_type.strip().lower() == (job_type or "").strip().lower()
    if total == 0:
        return None, 0, 0
    return satisfied / total, satisfied, total
