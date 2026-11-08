from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """User accounts, login, registration, password reset and roles."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
