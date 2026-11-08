from django.apps import AppConfig


class RecommendationsConfig(AppConfig):
    """Skill gaps, learning path, what-if and Top-K job recommendations."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "recommendations"
