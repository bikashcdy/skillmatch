import os

from rest_framework import serializers

from .models import Application


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
            "text_score",
            "experience_score",
            "education_score",
            "preference_score",
            "matched_skills",
            "partial_skills",
            "missing_skills",
            "knockout",
            "skill_gap",
            "status",
            "recruiter_note",
            "note_updated_at",
            "created_at",
        ]

    def get_resume_name(self, obj):
        return os.path.basename(obj.resume.file.name) if obj.resume.file else ""
