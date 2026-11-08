from django.apps import AppConfig


class ResumesConfig(AppConfig):
    """Resume upload, OCR, parsing and the candidate confirmation step."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "resumes"
