"""A simple resume quality check shown to candidates."""

import re

HEALTH_CHECKS = [
    # key, label, weight, fix tip
    ("email", "Email address", 10, "Add a professional email address near your name."),
    ("phone", "Phone number", 10, "Add your phone number (for example +977 98XXXXXXXX)."),
    ("skills_section", "Skills section", 15, "Add a clear 'Skills' heading and list your tools and technologies."),
    ("education", "Education", 10, "Add an 'Education' section with your degree and college."),
    ("experience", "Experience or internships", 10, "Add work, internship or volunteer experience, even short ones."),
    ("projects", "Projects", 15, "Add 2-3 projects with what you built and the technologies you used."),
    ("dates", "Dates and years", 10, "Add dates (2023-2024) so employers can see your timeline."),
    ("links", "GitHub / LinkedIn / portfolio link", 10, "Add your GitHub, LinkedIn or portfolio link."),
    ("length", "Enough detail (not too short)", 10, "Your resume is very short. Describe what you did in each project or job."),
]


def resume_health(text):
    """Score a resume out of 100 and say what to fix."""
    t = text or ""
    low = t.lower()
    words = len(re.findall(r"\w+", t))
    found = {
        "email": bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", t)),
        "phone": bool(re.search(r"(\+?977[\s-]?)?\b9[78]\d[\s-]?\d{3}[\s-]?\d{4}\b|\b\d{3}[\s-]?\d{3}[\s-]?\d{4}\b|\b0\d{1,2}[\s-]?\d{6,7}\b", t)),
        "skills_section": bool(re.search(r"\b(skills?|technical skills|technologies|expertise)\b", low)),
        "education": bool(re.search(r"\b(education|bachelor|master|diploma|college|university|campus|\+2|bca|bsc|bit|school)\b", low)),
        "experience": bool(re.search(r"\b(experience|intern|internship|worked|work history|employment|volunteer|freelanc)", low)),
        "projects": bool(re.search(r"\b(projects?|built|developed|created|designed)\b", low)),
        "dates": len(re.findall(r"\b(19|20)\d{2}\b", t)) >= 2,
        "links": bool(re.search(r"(github\.com|linkedin\.com|behance\.net|portfolio|gitlab\.com)", low)),
        "length": words >= 150,
    }
    checks, score = [], 0
    for key, label, weight, tip in HEALTH_CHECKS:
        ok = found[key]
        score += weight if ok else 0
        checks.append({"key": key, "label": label, "ok": ok, "tip": "" if ok else tip})
    if words > 1100:
        checks.append({"key": "too_long", "label": "Not too long", "ok": False,
                       "tip": "Your resume is long. Keep it to 1-2 pages."})
    return {"score": score, "words": words, "checks": checks}
