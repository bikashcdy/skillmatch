from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ADMIN = "admin"
    RECRUITER = "recruiter"
    CANDIDATE = "candidate"
    ROLE_CHOICES = [
        (ADMIN, "Admin"),
        (RECRUITER, "Recruiter"),
        (CANDIDATE, "Candidate"),
    ]

    role = models.CharField(max_length=12, choices=ROLE_CHOICES, default=CANDIDATE)
    company_name = models.CharField(max_length=150, blank=True)  # recruiters only
    is_approved = models.BooleanField(default=True)  # recruiters start unapproved until an admin approves
    # candidate job preferences (scored by the preference algorithm; both optional)
    preferred_location = models.CharField(max_length=100, blank=True)
    preferred_job_type = models.CharField(max_length=12, blank=True)

    class Meta(AbstractUser.Meta):
        app_label = "core"
