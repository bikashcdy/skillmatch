from django.db import models

from accounts.models import User


class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="resumes")
    file = models.FileField(upload_to="resumes/", blank=True)  # blank = entered manually
    raw_text = models.TextField(blank=True)
    extracted_skills = models.JSONField(default=list)
    experience_years = models.FloatField(default=0)
    education_level = models.CharField(max_length=50, blank=True)
    projects = models.JSONField(default=list)
    certifications = models.JSONField(default=list)
    confirmed = models.BooleanField(default=False)  # the candidate reviewed the scanned data
    confirmed_at = models.DateTimeField(null=True, blank=True)
    skills_edited = models.BooleanField(default=False)  # candidate changed the scanned skills
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core"
