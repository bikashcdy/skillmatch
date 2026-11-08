"""Resume use cases: scan a file, validate what the candidate confirms, build the response."""

from matching.engine import normalize_skill

from .extractors import extract_certifications, extract_education, extract_experience_years, extract_projects
from .parser import MIN_TEXT_CHARS, UnreadableResume, clean_text, extract_text, split_sections
from matching.engine import extract_skills


def parse_resume(resume):
    """Fill a Resume instance with extracted data (call after the file is saved)."""
    text = extract_text(resume.file.path)
    if len(text.strip()) < MIN_TEXT_CHARS:
        raise UnreadableResume(
            "We could not read any text from this resume. Please upload a clear "
            "PDF, DOCX or TXT file (or a sharp image of the resume), or enter your details manually."
        )
    text = clean_text(text)
    sections = split_sections(text)
    resume.raw_text = text
    resume.extracted_skills = extract_skills(text)
    resume.experience_years = extract_experience_years(text)
    resume.education_level = extract_education(text)
    resume.projects = extract_projects(sections)
    resume.certifications = extract_certifications(sections)
    resume.save()
    return resume


def text_list(value, label, errors, limit=12):
    if value in (None, ""):
        return []
    if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
        errors[label] = ["Send a list of short lines."]
        return []
    items = [" ".join(x.split())[:160] for x in value if x and x.strip()]
    return items[:limit]


def resume_payload(data):
    """Validate the details a candidate confirms (or types in by hand). Returns (values, errors)."""
    errors = {}
    raw = data.get("skills")
    skills = []
    if not isinstance(raw, list) or not all(isinstance(x, str) for x in raw):
        errors["skills"] = ["Send the skills as a list."]
    else:
        skills = sorted({normalize_skill(x) for x in raw if x and x.strip()})
        if any(len(x) > 40 for x in skills):
            errors["skills"] = ["A skill name is too long."]
        elif not skills:
            errors["skills"] = ["Add at least one skill."]
        elif len(skills) > 60:
            errors["skills"] = ["Keep it to 60 skills or fewer."]
    try:
        years = float(data.get("experience_years") or 0)
        if not 0 <= years <= 60:
            raise ValueError
    except (TypeError, ValueError):
        years = 0
        errors["experience_years"] = ["Enter years of experience between 0 and 60."]
    education = (data.get("education_level") or "none").strip().lower()
    if education not in ("none", "secondary", "diploma", "bachelor", "master", "phd"):
        errors["education_level"] = ["Choose a valid education level."]
    projects = text_list(data.get("projects"), "projects", errors)
    certs = text_list(data.get("certifications"), "certifications", errors)
    return {
        "extracted_skills": skills, "experience_years": years, "education_level": education,
        "projects": projects, "certifications": certs,
    }, errors
