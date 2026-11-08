from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    """Candidate profiles: job preferences and the confirmed skills."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "profiles"
