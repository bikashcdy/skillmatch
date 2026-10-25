from rest_framework import serializers

from .matching import normalize_skill
from .models import Application, Job, Resume, User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "role", "company_name"]

    def validate_role(self, value):
        # Admins are created with `createsuperuser`, never through public signup.
        if value not in (User.CANDIDATE, User.RECRUITER):
            raise serializers.ValidationError("Choose candidate or recruiter.")
        return value

    def create(self, data):
        return User.objects.create_user(**data)


class JobSerializer(serializers.ModelSerializer):
    applicants = serializers.IntegerField(source="applications.count", read_only=True)

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
            "is_open",
            "created_at",
            "applicants",
        ]
        read_only_fields = ["company", "created_at"]

    def validate_required_skills(self, value):
        return sorted({normalize_skill(s) for s in value if s.strip()})


class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = [
            "id",
            "file",
            "extracted_skills",
            "experience_years",
            "education_level",
            "uploaded_at",
        ]
        read_only_fields = [
            "extracted_skills",
            "experience_years",
            "education_level",
            "uploaded_at",
        ]


class ApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    company = serializers.CharField(source="job.company", read_only=True)
    candidate_name = serializers.CharField(source="candidate.username", read_only=True)
    candidate_email = serializers.CharField(source="candidate.email", read_only=True)

    class Meta:
        model = Application
        fields = [
            "id",
            "job",
            "job_title",
            "company",
            "candidate_name",
            "candidate_email",
            "match_percentage",
            "skill_score",
            "experience_score",
            "education_score",
            "matched_skills",
            "missing_skills",
            "status",
            "created_at",
        ]
