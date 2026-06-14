import re

from django.contrib.auth import authenticate, password_validation
from django.db import transaction
from rest_framework import serializers

from accounts.models import PhoneOTP, User
from accounts.services import generate_otp_code

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
    refresh = serializers.CharField(read_only=True)
    user = UserSerializer(read_only=True)


class MessageSerializer(serializers.Serializer):
    message = serializers.CharField(read_only=True)


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

    @transaction.atomic
    def save(self):
        data = self.validated_data
        phone_number = data["phone_number"]
        user = (
            User.objects.select_for_update().filter(phone_number=phone_number).first()
        )

        if user and user.is_phone_verified:
            raise serializers.ValidationError(
                {"phone_number": "A verified account already uses this phone number."}
            )

        profile = {
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "email": data.get("email", ""),
            "is_active": False,
            "is_phone_verified": False,
        }
        if user is None:
            user = User(phone_number=phone_number, **profile)
        else:
            for field, value in profile.items():
                setattr(user, field, value)

        user.set_password(data["password"])
        user.save()

        otp = PhoneOTP.objects.create(
            phone_number=phone_number,
            code=generate_otp_code(),
            purpose=PhoneOTP.Purpose.REGISTER,
            expires_at=PhoneOTP.expiration_time(),
        )
        return user, otp


class VerifyRegistrationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=11, validators=[validate_phone_number]
    )
    code = serializers.RegexField(r"^\d{6}$")

    @transaction.atomic
    def save(self):
        phone_number = self.validated_data["phone_number"]
        code = self.validated_data["code"]
        otp = (
            PhoneOTP.objects.select_for_update()
            .filter(
                phone_number=phone_number,
                purpose=PhoneOTP.Purpose.REGISTER,
                is_used=False,
            )
            .order_by("-created_at")
            .first()
        )

        if otp is None or otp.is_expired() or otp.code != code:
            raise serializers.ValidationError({"code": "Invalid or expired code."})

        user = (
            User.objects.select_for_update().filter(phone_number=phone_number).first()
        )
        if user is None:
            raise serializers.ValidationError(
                {"phone_number": "Registration was not found."}
            )

        otp.mark_used()
        user.is_phone_verified = True
        user.is_active = True
        user.save(update_fields=("is_phone_verified", "is_active"))
        return user


class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=11, validators=[validate_phone_number]
    )
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            phone_number=attrs["phone_number"],
            password=attrs["password"],
        )
        if user is None or not user.is_active or not user.is_phone_verified:
            raise serializers.ValidationError("Invalid phone number or password.")

        attrs["user"] = user
        return attrs
