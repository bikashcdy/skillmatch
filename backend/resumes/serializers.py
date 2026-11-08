import os

from rest_framework import serializers

from .models import Resume


class ResumeSerializer(serializers.ModelSerializer):
    filename = serializers.SerializerMethodField()
    applications = serializers.SerializerMethodField()
    manual = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = [
            "id",
            "filename",
            "extracted_skills",
            "experience_years",
            "education_level",
            "projects",
            "certifications",
            "confirmed",
            "manual",
            "uploaded_at",
            "applications",
        ]
        read_only_fields = fields

    def get_filename(self, obj):
        return os.path.basename(obj.file.name) if obj.file else ""

    def get_applications(self, obj):
        return obj.application_set.count()

    def get_manual(self, obj):
        return not obj.file
