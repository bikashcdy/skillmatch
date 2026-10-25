"""Resume parsing, skill extraction and job matching for SkillMatch AI."""

import os
import re

# canonical skill -> aliases. Extend this dictionary (or load it from the DB) as you grow.
SKILLS = {
    "python": ["python", "py"],
    "django": ["django", "drf", "django rest framework"],
    "flask": ["flask"],
    "javascript": ["javascript", "js", "es6"],
    "typescript": ["typescript", "ts"],
    "react": ["react", "reactjs", "react.js"],
    "node.js": ["node", "nodejs", "node.js"],
    "html": ["html", "html5"],
    "css": ["css", "css3", "tailwind", "bootstrap"],
    "sql": ["sql", "mysql", "postgresql", "postgres", "sqlite"],
    "mongodb": ["mongodb", "mongo"],
    "php": ["php", "laravel"],
    "java": ["java"],
    "c++": ["c++", "cpp"],
    "flutter": ["flutter", "dart"],
    "git": ["git", "github", "gitlab"],
    "docker": ["docker", "containers"],
    "aws": ["aws", "amazon web services"],
    "rest api": ["rest", "rest api", "restful", "api development"],
    "machine learning": ["machine learning", "ml", "scikit-learn", "sklearn"],
    "data analysis": [
        "data analysis",
        "pandas",
        "numpy",
        "excel",
        "power bi",
        "tableau",
    ],
    "testing": [
        "testing",
        "qa",
        "quality assurance",
        "selenium",
        "pytest",
        "unit testing",
    ],
    "communication": ["communication", "teamwork", "leadership"],
}

EDUCATION_LEVELS = {"none": 0, "diploma": 1, "bachelor": 2, "master": 3, "phd": 4}
EDUCATION_KEYWORDS = {
    "phd": ["phd", "ph.d", "doctorate"],
    "master": ["master", "msc", "m.sc", "mca", "mba", "m.tech"],
    "bachelor": [
        "bachelor",
        "bsc",
        "b.sc",
        "bca",
        "bba",
        "b.tech",
        "b.e.",
        "undergraduate",
    ],
    "diploma": ["diploma", "+2", "higher secondary", "a-level"],
}


IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
ALLOWED_EXTENSIONS = (".pdf", ".docx", ".txt") + IMAGE_EXTENSIONS
MIN_TEXT_CHARS = 40  # fewer characters than this means "no real text found"


class UnreadableResume(ValueError):
    """The uploaded resume contains no text we can read."""


class OCRUnavailable(UnreadableResume):
    """The file needs OCR (scanned image / photo) but OCR is not installed."""


def _require_ocr():
    """Import the optional OCR libraries or explain how to get them."""
    try:
        import pytesseract
        from PIL import Image
    except ImportError as e:
        raise OCRUnavailable(
            "This file is a scanned image or photo, and text recognition (OCR) "
            "is not installed on the server. Upload a PDF or DOCX that contains "
            "real text, or install OCR (see README: requirements-ocr.txt)."
        ) from e
    cmd = os.environ.get("TESSERACT_CMD")
    if not cmd and os.name == "nt":
        default = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        cmd = default if os.path.exists(default) else None
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd
    return pytesseract, Image


def _ocr_image(image):
    pytesseract, _ = _require_ocr()
    try:
        return pytesseract.image_to_string(image)
    except pytesseract.TesseractNotFoundError as e:
        raise OCRUnavailable(
            "The Tesseract OCR program is not installed. Install it from "
            "https://github.com/UB-Mannheim/tesseract/wiki and restart the server."
        ) from e


def _ocr_pdf(path):
    """OCR the page images embedded in an image-only PDF (a scan or a photo)."""
    import io

    from pypdf import PdfReader

    _, Image = _require_ocr()
    parts = []
    for page in PdfReader(path).pages:
        for embedded in page.images:
            img = Image.open(io.BytesIO(embedded.data)).convert("RGB")
            parts.append(_ocr_image(img))
    return "\n".join(parts)


def extract_text(path):
    """Return text from a .pdf, .docx, .txt or image file (OCR for scans/photos)."""
    lower = path.lower()
    if lower.endswith(".pdf"):
        from pypdf import PdfReader

        text = "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)
        if len(text.strip()) < MIN_TEXT_CHARS:  # image-only PDF, e.g. a photo
            text = _ocr_pdf(path)
        return text
    if lower.endswith(".docx"):
        import docx

        return "\n".join(p.text for p in docx.Document(path).paragraphs)
    if lower.endswith(IMAGE_EXTENSIONS):
        _, Image = _require_ocr()
        return _ocr_image(Image.open(path).convert("RGB"))
    with open(path, "r", errors="ignore") as f:
        return f.read()


def _has_term(text, term):
    pattern = r"(?<![\w+])" + re.escape(term) + r"(?![\w+])"
    return re.search(pattern, text) is not None


def extract_skills(text):
    text = text.lower()
    return sorted(
        skill
        for skill, aliases in SKILLS.items()
        if any(_has_term(text, a) for a in aliases)
    )


def normalize_skill(name):
    """Map a recruiter-typed skill ('ReactJS') to its canonical name."""
    n = name.strip().lower()
    for skill, aliases in SKILLS.items():
        if n == skill or n in aliases:
            return skill
    return n


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


def parse_resume(resume):
    """Fill a Resume instance with extracted data (call after the file is saved)."""
    text = extract_text(resume.file.path)
    if len(text.strip()) < MIN_TEXT_CHARS:
        raise UnreadableResume(
            "We could not read any text from this resume. Please upload a clear "
            "PDF, DOCX or TXT file (or a sharp image of the resume)."
        )
    resume.raw_text = text
    resume.extracted_skills = extract_skills(text)
    resume.experience_years = extract_experience_years(text)
    resume.education_level = extract_education(text)
    resume.save()
    return resume


# Weights must sum to 1.0
W_SKILLS, W_EXPERIENCE, W_EDUCATION = 0.60, 0.25, 0.15


def score_match(resume, job):
    """Return a dict with the overall match % and its breakdown."""
    required = {normalize_skill(s) for s in job.required_skills}
    have = set(resume.extracted_skills)
    matched = sorted(required & have)
    missing = sorted(required - have)

    skill_score = len(matched) / len(required) if required else 1.0

    if job.min_experience_years > 0:
        experience_score = min(resume.experience_years / job.min_experience_years, 1.0)
    else:
        experience_score = 1.0

    need = EDUCATION_LEVELS.get((job.required_education or "none").lower(), 0)
    got = EDUCATION_LEVELS.get(resume.education_level or "none", 0)
    education_score = 1.0 if need == 0 else min(got / need, 1.0)

    total = (
        W_SKILLS * skill_score
        + W_EXPERIENCE * experience_score
        + W_EDUCATION * education_score
    )
    return {
        "match_percentage": round(total * 100, 1),
        "skill_score": round(skill_score * 100, 1),
        "experience_score": round(experience_score * 100, 1),
        "education_score": round(education_score * 100, 1),
        "matched_skills": matched,
        "missing_skills": missing,
    }
