from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

iranian_mobile_validator = RegexValidator(
    regex=r"^09\d{9}$",
    message="Enter a valid Iranian mobile number starting with 09.",
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

    class DeliveryStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"
        UNCERTAIN = "uncertain", "Uncertain"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="registration_otps",
        blank=True,
        null=True,
    )
    phone_number = models.CharField(
        max_length=11,
        db_index=True,
        validators=(iranian_mobile_validator,),
    )
    code_hash = models.CharField(max_length=128, editable=False)
    pending_first_name = models.CharField(max_length=150, blank=True, editable=False)
    pending_last_name = models.CharField(max_length=150, blank=True, editable=False)
    pending_email = models.EmailField(blank=True, editable=False)
    pending_password_hash = models.CharField(
        max_length=128,
        blank=True,
        editable=False,
    )
    purpose = models.CharField(
        max_length=20,
        choices=Purpose.choices,
        default=Purpose.REGISTER,
    )
    is_used = models.BooleanField(default=False)
    delivery_status = models.CharField(
        max_length=10,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING,
    )
    failed_attempts = models.PositiveSmallIntegerField(default=0)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    invalidated_at = models.DateTimeField(blank=True, null=True)
    locked_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(
                fields=(
                    "phone_number",
                    "purpose",
                    "delivery_status",
                    "-created_at",
                ),
                name="phone_otp_lookup_idx",
            )
        ]

    def __str__(self):
        return f"{self.phone_number} ({self.purpose})"

    def is_expired(self):
        return timezone.now() >= self.expires_at


class LoginThrottle(models.Model):
    identifier_hash = models.CharField(max_length=64, unique=True)
    failed_attempts = models.PositiveSmallIntegerField(default=0)
    window_started_at = models.DateTimeField()
    blocked_until = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)

    def __str__(self):
        return f"Login throttle {self.pk}"
