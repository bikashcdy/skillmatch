import datetime

from django.db import models
from django.db.models import Q
from django.utils import timezone

from accounts.models import User

NEPAL_TZ = datetime.timezone(datetime.timedelta(hours=5, minutes=45))  # Nepal has no daylight saving


def nepal_today():
    """Today's date in Nepal, so a job expires at midnight Nepal time."""
    return timezone.now().astimezone(NEPAL_TZ).date()


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
    required_skills = models.JSONField(default=list)  # must-have skills, e.g. ["python", "django"]
    nice_to_have_skills = models.JSONField(default=list)  # bonus skills (count half as much)
    min_experience_years = models.FloatField(default=0)
    required_education = models.CharField(max_length=50, blank=True)  # e.g. "bachelor"
    job_type = models.CharField(max_length=12, choices=JOB_TYPES, default=FULL_TIME)
    salary_min = models.PositiveIntegerField(null=True, blank=True)  # NPR per month
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    expires_at = models.DateField(null=True, blank=True)  # last day to apply; empty = no deadline
    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} @ {self.company}"

    @property
    def is_expired(self):
        return bool(self.expires_at and self.expires_at < nepal_today())

    @classmethod
    def active(cls):
        """Open jobs whose deadline has not passed. Expired jobs vanish for candidates automatically."""
        return (
            cls.objects.filter(is_open=True, recruiter__is_approved=True, recruiter__is_active=True)
            .filter(Q(expires_at__isnull=True) | Q(expires_at__gte=nepal_today()))
        )

    class Meta:
        app_label = "core"
