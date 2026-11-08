"""Reading resume files (PDF, DOCX, TXT, photos) and cleaning the text."""

import re

from .ocr import OCRUnavailable as _OCRMissing
from .ocr import read_image_file, read_pdf

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
ALLOWED_EXTENSIONS = (".pdf", ".docx", ".txt") + IMAGE_EXTENSIONS
MIN_TEXT_CHARS = 40  # fewer characters than this means "no real text found"


class UnreadableResume(ValueError):
    """The uploaded resume contains no text we can read."""


class OCRUnavailable(UnreadableResume):
    """The file needs OCR (scanned image / photo) but OCR is not installed."""


def extract_text(path):
    """Return text from a .pdf, .docx, .txt or image file (OCR for scans/photos)."""
    lower = path.lower()
    try:
        return _extract_text(path, lower)
    except _OCRMissing as e:  # scanned file but no OCR available: a clear message instead of a crash
        raise OCRUnavailable(str(e)) from e


def _extract_text(path, lower):
    if lower.endswith(".pdf"):
        return read_pdf(path)  # real text where there is any, OCR for picture-only pages
    if lower.endswith(".docx"):
        import docx

        return "\n".join(p.text for p in docx.Document(path).paragraphs)
    if lower.endswith(IMAGE_EXTENSIONS):
        return read_image_file(path)
    with open(path, "r", errors="ignore") as f:
        return f.read()


_SECTION_HEADINGS = {
    "skills": ("skills", "technical skills", "key skills", "core skills", "technologies", "expertise"),
    "education": ("education", "academic background", "qualification", "qualifications", "academics"),
    "experience": ("experience", "work experience", "professional experience", "employment", "work history", "internship", "internships"),
    "projects": ("projects", "project", "academic projects", "personal projects", "key projects"),
    "certifications": ("certifications", "certification", "certificates", "certificate", "courses", "licenses", "training"),
}


_HEADING_LOOKUP = {h: key for key, names in _SECTION_HEADINGS.items() for h in names}


def clean_text(text):
    """Tidy extracted text: one space between words, no odd symbols, consistent line breaks."""
    text = (text or "").replace("\r", "\n").replace("\u2022", "\n- ").replace("\u25cf", "\n- ").replace("\t", " ")
    text = re.sub(r"[^\w\s@.,:;+#/&()%\-\']", " ", text)  # drop unwanted special characters
    lines = [re.sub(r"[ ]{2,}", " ", line).strip() for line in text.split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def split_sections(text):
    """Split resume text into Skills, Education, Experience, Projects and Certifications blocks."""
    sections, current = {}, None
    for line in (text or "").split("\n"):
        heading = re.sub(r"[^a-z ]", "", line.lower()).strip()
        if heading in _HEADING_LOOKUP and len(line.strip()) <= 40:
            current = _HEADING_LOOKUP[heading]
            sections.setdefault(current, [])
        elif current and line.strip():
            sections[current].append(line.strip())
    return {k: v for k, v in sections.items() if v}


def _items(lines, limit=12):
    items = []
    for line in lines:
        line = re.sub(r"^[-*\d.)\s]+", "", line).strip()
        if len(line) >= 4:
            items.append(line[:160])
    return items[:limit]
