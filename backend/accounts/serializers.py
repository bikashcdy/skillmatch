from rest_framework import serializers

from . import validators as V
from .models import User


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
