from django.db import models

from jobs.models import Job
from resumes.models import Resume


class WeightConfig(models.Model):
    """A saved set of matching weights. Only one is active; none active means the defaults are used."""

    version = models.PositiveIntegerField(unique=True)
    weights = models.JSONField()  # {"skill": 0.4, "text": 0.2, ...}
    tuning_ndcg = models.FloatField(null=True, blank=True)
    test_ndcg = models.FloatField(null=True, blank=True)
    note = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core"
        ordering = ["-version"]


class RelevanceRating(models.Model):
    """A manual rating (0-3) of how well a resume fits a job. Used to tune and evaluate the weights."""

    TUNE, TEST = "tune", "test"
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="ratings")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="ratings")
    rating = models.PositiveSmallIntegerField()  # 0 = not relevant ... 3 = perfect fit
    split = models.CharField(max_length=4, default=TUNE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core"
        unique_together = ("resume", "job")
