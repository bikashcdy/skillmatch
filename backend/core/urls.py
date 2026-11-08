"""All API routes. Each app owns its own urls.py; this file only joins them under /api/."""

from django.urls import include, path

urlpatterns = [
    path("", include("accounts.urls")),
    path("", include("profiles.urls")),
    path("", include("resumes.urls")),
    path("", include("jobs.urls")),
    path("", include("applications.urls")),
    path("", include("matching.urls")),
    path("", include("recommendations.urls")),
    path("", include("analytics.urls")),
]
