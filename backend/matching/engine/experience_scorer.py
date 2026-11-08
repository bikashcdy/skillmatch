"""Experience score: S_exp = min(candidate years / required years, 1)."""


def score_experience(candidate_years, required_years):
    required = float(required_years or 0)
    if required <= 0:  # the job does not ask for experience (fresher friendly)
        return 1.0
    return min(float(candidate_years or 0) / required, 1.0)
