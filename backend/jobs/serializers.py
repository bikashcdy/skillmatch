from rest_framework import serializers

from matching.engine import normalize_skill

from . import validators as V
from .models import Job, nepal_today


class JobSerializer(serializers.ModelSerializer):
    applicants = serializers.IntegerField(source="applications.count", read_only=True)
    my_application = serializers.SerializerMethodField()
    resume_match = serializers.SerializerMethodField()
    is_expired = serializers.BooleanField(read_only=True)
    days_left = serializers.SerializerMethodField()
    match_detail = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            "id",
            "title",
            "company",
            "description",
            "location",
            "required_skills",
            "nice_to_have_skills",
            "min_experience_years",
            "required_education",
            "job_type",
            "salary_min",
            "salary_max",
            "expires_at",
            "is_expired",
            "days_left",
            "match_detail",
            "is_open",
            "created_at",
            "applicants",
            "my_application",
            "resume_match",
        ]
        read_only_fields = ["company", "created_at"]

    def validate_title(self, value):
        errors = V.job_title_errors(value)
        if errors:
            raise serializers.ValidationError(errors)
        return " ".join(value.split())

    def validate_description(self, value):
        errors = V.job_description_errors(value)
        if errors:
            raise serializers.ValidationError(errors)
        return value.strip()

    def validate_location(self, value):
        errors = V.job_location_errors(value)
        if errors:
            raise serializers.ValidationError(errors)
        return " ".join(value.split())

    def validate_required_skills(self, value):
        cleaned = sorted({normalize_skill(s) for s in value if s and s.strip()})
        if not cleaned:
            raise serializers.ValidationError("Add at least one required skill.")
        return cleaned

    def validate_nice_to_have_skills(self, value):
        return sorted({normalize_skill(s) for s in value if s and s.strip()})

    def validate_min_experience_years(self, value):
        if value < 0:
            raise serializers.ValidationError("Experience cannot be negative.")
        return value

    def get_days_left(self, job):
        if not job.expires_at:
            return None
        return (job.expires_at - nepal_today()).days

    def get_match_detail(self, job):
        return (self.context.get("match_detail") or {}).get(job.id)

    def validate_expires_at(self, value):
        # a new/changed deadline cannot be in the past
        if self.instance and self.instance.expires_at == value:
            return value  # unchanged deadline on an old job is fine
        if value and value < nepal_today():
            raise serializers.ValidationError("The expiry date cannot be in the past.")
        return value

    def validate(self, attrs):
        # a skill is either must-have or nice-to-have, never both
        if "nice_to_have_skills" in attrs:
            must = set(attrs.get("required_skills") or (self.instance.required_skills if self.instance else []))
            attrs["nice_to_have_skills"] = [s for s in attrs["nice_to_have_skills"] if s not in must]
        lo, hi = attrs.get("salary_min"), attrs.get("salary_max")
        if lo is not None and hi is not None and hi < lo:
            raise serializers.ValidationError({"salary_max": "Maximum salary must be at least the minimum."})
        return attrs

    def get_my_application(self, job):
        apps = self.context.get("my_apps")
        app = apps.get(job.id) if apps else None
        if not app:
            return None
        return {"id": app.id, "status": app.status, "match_percentage": app.match_percentage}

    def get_resume_match(self, job):
        matches = self.context.get("match_map")
        return matches.get(job.id) if matches else None
