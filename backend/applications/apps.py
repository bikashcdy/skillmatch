from django.apps import AppConfig


class ApplicationsConfig(AppConfig):
    """Job applications, recruiter decisions and notifications."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "applications"
