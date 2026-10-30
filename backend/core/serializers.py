import os

from rest_framework import serializers

from . import validators as V
from .matching import normalize_skill
from .models import Application, Job, Resume, User, nepal_today


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "role", "company_name"]
        extra_kwargs = {"email": {"required": True, "allow_blank": False}, "username": {"validators": []}}

    def validate_username(self, value):
        errors = V.username_errors(value)
        if errors:
            raise serializers.ValidationError(errors)
        if User.objects.filter(username__iexact=value.strip()).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value.strip()

    def validate_email(self, value):
        errors = V.email_errors(value)
        if errors:
            raise serializers.ValidationError(errors)
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_role(self, value):
        # Admins are created with `createsuperuser`, never through public signup.
        if value not in (User.CANDIDATE, User.RECRUITER):
            raise serializers.ValidationError("Choose candidate or recruiter.")
        return value

    def validate(self, attrs):
        errors = V.password_errors(attrs.get("password"), attrs.get("username", ""), attrs.get("email", ""))
        if errors:
            raise serializers.ValidationError({"password": errors})
        if attrs.get("role") == User.RECRUITER:
            company = V.company_errors(attrs.get("company_name"))
            if company:
                raise serializers.ValidationError({"company_name": company})
            attrs["company_name"] = attrs["company_name"].strip()
        else:
            attrs["company_name"] = ""
        return attrs

    def create(self, data):
        recruiter = data.get("role") == User.RECRUITER
        return User.objects.create_user(**data, is_approved=not recruiter)  # recruiters wait for an admin


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

    def validate_required_skills(self, value):
        cleaned = sorted({normalize_skill(s) for s in value if s and s.strip()})
        if not cleaned:
            raise serializers.ValidationError("Add at least one required skill.")
        return cleaned

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


class ResumeSerializer(serializers.ModelSerializer):
    filename = serializers.SerializerMethodField()
    applications = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = [
            "id",
            "filename",
            "extracted_skills",
            "experience_years",
            "education_level",
            "uploaded_at",
            "applications",
        ]
        read_only_fields = fields

    def get_filename(self, obj):
        return os.path.basename(obj.file.name) if obj.file else ""

    def get_applications(self, obj):
        return obj.application_set.count()


class ApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    job_location = serializers.CharField(source="job.location", read_only=True)
    company = serializers.CharField(source="job.company", read_only=True)
    candidate_name = serializers.CharField(source="candidate.username", read_only=True)
    candidate_email = serializers.CharField(source="candidate.email", read_only=True)
    resume_name = serializers.SerializerMethodField()
    candidate_skills = serializers.JSONField(source="resume.extracted_skills", read_only=True)
    candidate_experience = serializers.FloatField(source="resume.experience_years", read_only=True)
    candidate_education = serializers.CharField(source="resume.education_level", read_only=True)

    class Meta:
        model = Application
        fields = [
            "id",
            "job",
            "job_title",
            "job_location",
            "company",
            "candidate_name",
            "candidate_email",
            "candidate_skills",
            "candidate_experience",
            "candidate_education",
            "resume",
            "resume_name",
            "match_percentage",
            "skill_score",
            "experience_score",
            "education_score",
            "matched_skills",
            "missing_skills",
            "status",
            "recruiter_note",
            "note_updated_at",
            "created_at",
        ]

    def get_resume_name(self, obj):
        return os.path.basename(obj.resume.file.name) if obj.resume.file else ""
