"""Rules for posting a job. The React form shows the same rules live."""

import re


def job_title_errors(value):
    v = " ".join((value or "").split())
    if not v:
        return ["Job title is required."]
    errors = []
    if not 3 <= len(v) <= 80:
        errors.append("Job title must be 3-80 characters.")
    if re.search(r"\d", v):
        errors.append("Job title cannot contain numbers.")
    if re.search(r"[^A-Za-z\s&.,/+#()\-]", re.sub(r"\d", "", v)):
        errors.append("Job title can only use letters and & . , / + # ( ) -")
    if len(re.findall(r"[A-Za-z]", v)) < 3:
        errors.append("Job title must contain real words, for example Python Developer.")
    return errors


def job_description_errors(value):
    v = (value or "").strip()
    if not v:
        return ["Description is required."]
    errors = []
    if len(v) < 30:
        errors.append("Description must be at least 30 characters.")
    if len(v) > 3000:
        errors.append("Description must be at most 3000 characters.")
    words = re.findall(r"[A-Za-z]{2,}", v)
    if len(words) < 5:
        errors.append("Description needs at least 5 real words, not just numbers or symbols.")
    elif len(set(w.lower() for w in words)) < 4:
        errors.append("Description looks repeated. Describe the role, duties and requirements.")
    return errors


def job_location_errors(value):
    v = " ".join((value or "").split())
    if not v:
        return ["Location is required."]
    errors = []
    if not 2 <= len(v) <= 60:
        errors.append("Location must be 2-60 characters.")
    if re.search(r"[^A-Za-z\s.,\-]", v):
        errors.append("Location can only contain letters (no numbers or symbols).")
    return errors
