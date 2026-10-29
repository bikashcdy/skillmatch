import os

from rest_framework import serializers

from .matching import normalize_skill
from .models import Application, Job, Resume, User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "role", "company_name"]
        extra_kwargs = {"email": {"required": True, "allow_blank": False}}

    def validate_role(self, value):
        # Admins are created with `createsuperuser`, never through public signup.
        if value not in (User.CANDIDATE, User.RECRUITER):
            raise serializers.ValidationError("Choose candidate or recruiter.")
        return value

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate(self, attrs):
        if attrs.get("role") == User.RECRUITER:
            if not (attrs.get("company_name") or "").strip():
                raise serializers.ValidationError(
                    {"company_name": "Company name is required for recruiters."}
                )
        else:
            attrs["company_name"] = ""
        return attrs

    def create(self, data):
        return User.objects.create_user(**data)


class JobSerializer(serializers.ModelSerializer):
    applicants = serializers.IntegerField(source="applications.count", read_only=True)
    my_application = serializers.SerializerMethodField()
    resume_match = serializers.SerializerMethodField()
    saved = serializers.SerializerMethodField()

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
            "is_open",
            "created_at",
            "applicants",
            "my_application",
            "resume_match",
            "saved",
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

    def validate(self, attrs):
        lo, hi = attrs.get("salary_min"), attrs.get("salary_max")
        if lo is not None and hi is not None and hi < lo:
            raise serializers.ValidationError({"salary_max": "Maximum salary must be at least the minimum."})
        return attrs

    def get_saved(self, job):
        return job.id in (self.context.get("saved_ids") or ())

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
    file = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = [
            "id",
            "file",
            "filename",
            "extracted_skills",
            "experience_years",
            "education_level",
            "uploaded_at",
        ]
        read_only_fields = fields

    def get_filename(self, obj):
        return os.path.basename(obj.file.name) if obj.file else ""

    def get_file(self, obj):
        if not obj.file:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.file.url) if request else obj.file.url


class ApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    job_location = serializers.CharField(source="job.location", read_only=True)
    company = serializers.CharField(source="job.company", read_only=True)
    candidate_name = serializers.CharField(source="candidate.username", read_only=True)
    candidate_email = serializers.CharField(source="candidate.email", read_only=True)
    resume_url = serializers.SerializerMethodField()
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
            "resume_url",
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

    def get_resume_url(self, obj):
        if not obj.resume.file:
            return None
        request = self.context.get("request")
        url = obj.resume.file.url
        return request.build_absolute_uri(url) if request else url

    def get_resume_name(self, obj):
        return os.path.basename(obj.resume.file.name) if obj.resume.file else ""
