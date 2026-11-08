"""MatchEngine: combines five scoring algorithms into one explainable match percentage.

M = 100 x (w1 S_skill + w2 S_text + w3 S_exp + w4 S_edu + w5 S_pref)
If a must-have skill is completely missing the score is capped at 60 (knock-out).
"""

from dataclasses import dataclass, field

from .education_scorer import score_education
from .experience_scorer import score_experience
from .preference_scorer import score_preferences
from .skill_gap import skill_gap_percentage
from .skill_scorer import score_skills
from .text_scorer import TextScorer

COMPONENTS = ("skill", "text", "experience", "education", "preference")
DEFAULT_WEIGHTS = {"skill": 0.40, "text": 0.20, "experience": 0.20, "education": 0.10, "preference": 0.10}
KNOCKOUT_CAP = 60.0


@dataclass
class CandidateProfile:
    skills: list = field(default_factory=list)
    experience_years: float = 0.0
    education_level: str = ""
    text: str = ""  # full resume text, used for TF-IDF similarity
    preferred_location: str = ""
    preferred_job_type: str = ""


def job_text(job):
    """The text of a job posting used for TF-IDF: title, description and skill names."""
    skills = list(job.required_skills or []) + list(getattr(job, "nice_to_have_skills", None) or [])
    return " ".join([job.title or "", job.description or "", " ".join(skills)])


def normalize_weights(weights):
    cleaned = {k: max(float(weights.get(k, 0)), 0.0) for k in COMPONENTS}
    total = sum(cleaned.values())
    if total <= 0:
        return dict(DEFAULT_WEIGHTS)
    return {k: v / total for k, v in cleaned.items()}


def combine(components, weights, knockout=False):
    """Weighted sum of the component scores (each 0..1 or None) as a percentage.

    A component that is None (for example preferences the candidate never set) is left out and
    the remaining weights are scaled up so a candidate is not punished for not filling it in.
    """
    active = {k: weights[k] for k in COMPONENTS if components.get(k) is not None and weights.get(k, 0) > 0}
    total_weight = sum(active.values())
    if total_weight <= 0:
        raw = 0.0
    else:
        raw = 100.0 * sum(w * components[k] for k, w in active.items()) / total_weight
    return (min(raw, KNOCKOUT_CAP) if knockout else raw), raw


class MatchEngine:
    def __init__(self, weights=None, text_scorer=None):
        self.weights = normalize_weights(weights or DEFAULT_WEIGHTS)
        self.text_scorer = text_scorer  # shared TextScorer built from all job texts (optional)

    def components(self, candidate, job):
        skills = score_skills(candidate.skills, job.required_skills, getattr(job, "nice_to_have_skills", None) or [])
        scorer = self.text_scorer or TextScorer()
        text = scorer.similarity(candidate.text or "", job_text(job)) if (candidate.text or "").strip() else 0.0
        pref, pref_ok, pref_total = score_preferences(
            candidate.preferred_location, candidate.preferred_job_type, job.location, job.job_type
        )
        values = {
            "skill": skills["score"],
            "text": text,
            "experience": score_experience(candidate.experience_years, job.min_experience_years),
            "education": score_education(candidate.education_level, job.required_education),
            "preference": pref,
        }
        return values, skills, (pref_ok, pref_total)

    def calculate(self, candidate, job):
        values, skills, (pref_ok, pref_total) = self.components(candidate, job)
        final, raw = combine(values, self.weights, knockout=skills["knockout"])
        gap = skill_gap_percentage(skills["missing"], skills["total_skills"])
        explanation = []
        if skills["knockout"]:
            explanation.append(
                "Missing must-have skill(s): " + ", ".join(skills["missing_must_have"]) +
                f". The score is capped at {KNOCKOUT_CAP:g}% (it would be {raw:.0f}% otherwise)."
            )
        for skill, other in skills["related_to"].items():
            explanation.append(f"{skill}: related skill {other} gives half credit.")
        if values["preference"] is None:
            explanation.append("No job preferences set, so preferences are not counted.")
        pct = lambda v: None if v is None else round(v * 100, 1)  # noqa: E731
        return {
            "match_percentage": round(final, 1),
            "raw_percentage": round(raw, 1),
            "skill_score": pct(values["skill"]),
            "text_score": pct(values["text"]),
            "experience_score": pct(values["experience"]),
            "education_score": pct(values["education"]),
            "preference_score": pct(values["preference"]),
            "matched_skills": skills["matched"],
            "partial_skills": skills["partial"],
            "missing_skills": skills["missing"],
            "missing_must_have": skills["missing_must_have"],
            "knockout": skills["knockout"],
            "skill_gap": gap,
            "weights": {k: round(v, 3) for k, v in self.weights.items()},
            "explanation": explanation,
        }
