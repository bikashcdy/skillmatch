from django.db import models

from accounts.models import User
from jobs.models import Job
from resumes.models import Resume


class Application(models.Model):
    APPLIED = "applied"
    AUTO = "auto"
    SELECTED = "selected"
    REJECTED = "rejected"
    STATUS_CHOICES = [
        (APPLIED, "Applied"),
        (AUTO, "Auto-applied (related job)"),
        (SELECTED, "Selected"),
        (REJECTED, "Rejected"),
    ]

    candidate = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="applications"
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    match_percentage = models.FloatField(default=0)
    skill_score = models.FloatField(default=0)
    text_score = models.FloatField(null=True, blank=True)
    experience_score = models.FloatField(default=0)
    education_score = models.FloatField(default=0)
    preference_score = models.FloatField(null=True, blank=True)  # empty = candidate set no preferences
    matched_skills = models.JSONField(default=list)
    partial_skills = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)
    knockout = models.BooleanField(default=False)  # a must-have skill is missing: score capped at 60
    skill_gap = models.FloatField(default=0)  # % of the job's skills the candidate does not have
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=APPLIED)
    recruiter_note = models.TextField(blank=True)  # short message from the recruiter
    note_updated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core"
        unique_together = ("candidate", "job")
        ordering = ["-match_percentage"]
