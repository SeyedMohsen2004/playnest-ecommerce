import re

from django.contrib.auth import password_validation
from rest_framework import serializers

from accounts.models import User

IRANIAN_MOBILE_PATTERN = re.compile(r"^09\d{9}$")


def validate_phone_number(value):
    if not IRANIAN_MOBILE_PATTERN.fullmatch(value):
        raise serializers.ValidationError(
            "Enter a valid Iranian mobile number starting with 09."
        )
    return value


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "phone_number",
            "first_name",
            "last_name",
            "email",
            "is_phone_verified",
            "date_joined",
        )
        read_only_fields = fields


class AuthResponseSerializer(serializers.Serializer):
    access = serializers.CharField(read_only=True)
    user = UserSerializer(read_only=True)


class AccessTokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField(read_only=True)


class MessageSerializer(serializers.Serializer):
    message = serializers.CharField(read_only=True)


class PendingRegistrationResponseSerializer(MessageSerializer):
    retry_after = serializers.IntegerField(read_only=True, min_value=1)


class ErrorResponseSerializer(serializers.Serializer):
    detail = serializers.CharField(read_only=True)
    retry_after = serializers.IntegerField(
        read_only=True,
        required=False,
        min_value=1,
    )


class CSRFTokenResponseSerializer(serializers.Serializer):
    csrf_token = serializers.CharField(read_only=True)


class RegisterSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=11, validators=[validate_phone_number]
    )
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        password_validation.validate_password(attrs["password"])
        return attrs


class VerifyRegistrationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=11, validators=[validate_phone_number]
    )
    code = serializers.RegexField(r"^\d{6}$", write_only=True)


class ResendRegistrationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=11, validators=[validate_phone_number]
    )


class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=11, validators=[validate_phone_number]
    )
    password = serializers.CharField(write_only=True)
