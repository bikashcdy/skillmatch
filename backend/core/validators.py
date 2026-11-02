"""Registration rules. Used by the API (serializers/views); the React form shows the same rules live.

Change the numbers here to change the rules everywhere on the server.
"""

import re

USERNAME_MIN, USERNAME_MAX = 4, 20
PASSWORD_MIN, PASSWORD_MAX = 8, 64
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")


def username_errors(value):
    v = value or ""
    errors = []
    if not v.strip():
        return ["Username is required."]
    if v != v.strip() or " " in v:
        errors.append("Username cannot contain spaces.")
    if not USERNAME_MIN <= len(v.strip()) <= USERNAME_MAX:
        errors.append(f"Username must be {USERNAME_MIN}-{USERNAME_MAX} characters.")
    if not re.fullmatch(r"[A-Za-z0-9_]*", v.replace(" ", "")):
        errors.append("Username can only use letters, numbers and underscore (_).")
    if v.strip() and not v.strip()[0].isalpha():
        errors.append("Username must start with a letter.")
    return errors


def email_errors(value):
    v = (value or "").strip()
    if not v:
        return ["Email is required."]
    if len(v) > 254 or not EMAIL_RE.match(v) or ".." in v:
        return ["Enter a valid email address, for example name@gmail.com."]
    return []


def password_errors(value, username="", email=""):
    v = value or ""
    errors = []
    if not v:
        return ["Password is required."]
    if " " in v:
        errors.append("Password cannot contain spaces.")
    if not PASSWORD_MIN <= len(v) <= PASSWORD_MAX:
        errors.append(f"Password must be {PASSWORD_MIN}-{PASSWORD_MAX} characters.")
    if not re.search(r"[A-Z]", v):
        errors.append("Password needs at least one uppercase letter (A-Z).")
    if not re.search(r"[a-z]", v):
        errors.append("Password needs at least one lowercase letter (a-z).")
    if not re.search(r"\d", v):
        errors.append("Password needs at least one number (0-9).")
    if not re.search(r"[^A-Za-z0-9]", v):
        errors.append("Password needs at least one special character (for example @ # $ !).")
    if username and len(username) >= 3 and username.lower() in v.lower():
        errors.append("Password cannot contain your username.")
    local = (email or "").split("@")[0]
    if local and len(local) >= 4 and local.lower() in v.lower():
        errors.append("Password cannot contain the first part of your email.")
    return errors


def company_errors(value):
    v = (value or "").strip()
    if len(v) < 2 or len(v) > 100:
        return ["Company name must be 2-100 characters."]
    return []


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
