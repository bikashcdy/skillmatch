# ---- Paste this block at the BOTTOM of backend/config/settings.py ----
# Everything reads environment variables, so on your own PC (no variables set)
# nothing changes. Emails are printed in the backend terminal until you add
# EMAIL_HOST_USER / EMAIL_HOST_PASSWORD.
import os

DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", SECRET_KEY)
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Where the React app lives (used for links inside emails and for CORS).
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
if os.environ.get("FRONTEND_URL"):
    CORS_ALLOWED_ORIGINS = list(CORS_ALLOWED_ORIGINS) + [FRONTEND_URL]
    CSRF_TRUSTED_ORIGINS = [FRONTEND_URL]

# Real emails (Gmail example: turn on 2-step verification, then create an "App password").
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")          # you@gmail.com
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")  # 16-character app password
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", f"JobMitra <{EMAIL_HOST_USER or 'noreply@localhost'}>")

# Production database from environment (only used when DB_NAME is set).
if os.environ.get("DB_NAME"):
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ["DB_NAME"],
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
        "PORT": os.environ.get("DB_PORT", "3306"),
    }
