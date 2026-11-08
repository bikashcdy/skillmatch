"""Pull structured facts out of resume text: experience, education, projects, certifications."""

import re

from .parser import _items

from matching.engine import extract_skills
from matching.engine.skill_data import EDUCATION_KEYWORDS, EDUCATION_LEVELS

def extract_experience_years(text):
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)", text.lower())
    return max((float(m) for m in matches), default=0.0)


def extract_education(text):
    text = text.lower()
    best = "none"
    for level, words in EDUCATION_KEYWORDS.items():
        if (
            any(w in text for w in words)
            and EDUCATION_LEVELS[level] > EDUCATION_LEVELS[best]
        ):
            best = level
    return best


def extract_projects(sections):
    return _items(sections.get("projects", []))


def extract_certifications(sections):
    return _items(sections.get("certifications", []))


def candidate_text(resume):
    """The text used for TF-IDF similarity. Manually entered resumes have no file, so build it."""
    if resume.raw_text:
        return resume.raw_text
    return " ".join(
        list(resume.extracted_skills or []) + list(resume.projects or []) + list(resume.certifications or [])
        + [resume.education_level or ""]
    )


def refresh_skills(resume):
    """Re-scan the stored text so old resumes benefit from newer skill lists.

    A resume whose skills the candidate edited by hand is left alone.
    """
    if not resume.raw_text or resume.skills_edited:
        return resume
    skills = extract_skills(resume.raw_text)
    if skills != resume.extracted_skills:
        resume.extracted_skills = skills
        resume.save(update_fields=["extracted_skills"])
    return resume
