from datetime import timedelta

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

iranian_mobile_validator = RegexValidator(
    regex=r"^09\d{9}$",
    message="Enter a valid Iranian mobile number starting with 09.",
)
otp_code_validator = RegexValidator(
    regex=r"^\d{6}$",
    message="OTP code must contain exactly 6 digits.",
)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("The phone number must be provided.")
        if not password:
            raise ValueError("The password must be provided.")

        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_phone_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    phone_number = models.CharField(
        max_length=11,
        unique=True,
        validators=(iranian_mobile_validator,),
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    is_phone_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ("-date_joined",)

    def __str__(self):
        return self.phone_number

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name


class PhoneOTP(models.Model):
    class Purpose(models.TextChoices):
        REGISTER = "register", "Register"

    phone_number = models.CharField(
        max_length=11,
        db_index=True,
        validators=(iranian_mobile_validator,),
    )
    code = models.CharField(max_length=6, validators=(otp_code_validator,))
    purpose = models.CharField(
        max_length=20,
        choices=Purpose.choices,
        default=Purpose.REGISTER,
    )
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(
                fields=("phone_number", "purpose", "is_used", "-created_at"),
                name="phone_otp_lookup_idx",
            )
        ]

    def __str__(self):
        return f"{self.phone_number} ({self.purpose})"

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def mark_used(self):
        self.is_used = True
        self.verified_at = timezone.now()
        self.save(update_fields=("is_used", "verified_at"))

    @classmethod
    def expiration_time(cls):
        return timezone.now() + timedelta(minutes=2)
