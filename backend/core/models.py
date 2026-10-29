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
    email_alerts = models.BooleanField(default=True)  # candidates: new-job match emails


class Job(models.Model):
    FULL_TIME, PART_TIME, INTERNSHIP, CONTRACT = "full_time", "part_time", "internship", "contract"
    JOB_TYPES = [
        (FULL_TIME, "Full-time"),
        (PART_TIME, "Part-time"),
        (INTERNSHIP, "Internship"),
        (CONTRACT, "Contract"),
    ]

    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="jobs")
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=150)
    description = models.TextField()
    location = models.CharField(max_length=150, blank=True)
    required_skills = models.JSONField(default=list)  # ["python", "django"]
    min_experience_years = models.FloatField(default=0)
    required_education = models.CharField(max_length=50, blank=True)  # e.g. "bachelor"
    job_type = models.CharField(max_length=12, choices=JOB_TYPES, default=FULL_TIME)
    salary_min = models.PositiveIntegerField(null=True, blank=True)  # NPR per month
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} @ {self.company}"


class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="resumes")
    file = models.FileField(upload_to="resumes/")
    raw_text = models.TextField(blank=True)
    extracted_skills = models.JSONField(default=list)
    experience_years = models.FloatField(default=0)
    education_level = models.CharField(max_length=50, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)


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
    experience_score = models.FloatField(default=0)
    education_score = models.FloatField(default=0)
    matched_skills = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=APPLIED)
    recruiter_note = models.TextField(blank=True)  # short message from the recruiter
    note_updated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("candidate", "job")
        ordering = ["-match_percentage"]


class SavedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_jobs")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="saved_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "job")
        ordering = ["-created_at"]
