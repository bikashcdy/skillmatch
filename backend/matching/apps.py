from django.apps import AppConfig


class MatchingConfig(AppConfig):
    """The matching engine, weight tuning and evaluation."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "matching"
