import logging
import secrets
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from hashlib import sha256
from hmac import new as hmac_new

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.utils import timezone

from accounts.models import LoginThrottle, PhoneOTP, User

logger = logging.getLogger(__name__)


class SMSDeliveryError(RuntimeError):
    """Raised when an SMS provider cannot deliver an OTP."""


def generate_otp_code():
    return f"{secrets.randbelow(1_000_000):06d}"


def _send_kavenegar_otp(phone_number, code):
    if not settings.KAVENEGAR_API_KEY:
        raise ImproperlyConfigured(
            "KAVENEGAR_API_KEY is required when SMS_PROVIDER is 'kavenegar'."
        )

    if not settings.KAVENEGAR_VERIFY_TEMPLATE and not settings.KAVENEGAR_SENDER:
        raise ImproperlyConfigured(
            "KAVENEGAR_SENDER is required when no KAVENEGAR_VERIFY_TEMPLATE is set."
        )

    try:
        from kavenegar import KavenegarAPI

        api = KavenegarAPI(settings.KAVENEGAR_API_KEY)
        if settings.KAVENEGAR_VERIFY_TEMPLATE:
            return api.verify_lookup(
                {
                    "receptor": phone_number,
                    "token": code,
                    "template": settings.KAVENEGAR_VERIFY_TEMPLATE,
                }
            )

        return api.sms_send(
            {
                "sender": settings.KAVENEGAR_SENDER,
                "receptor": phone_number,
                "message": f"IpakToys verification code: {code}",
            }
        )
    except Exception as exc:
        logger.error("Kavenegar failed to deliver an OTP.")
        raise SMSDeliveryError("The SMS provider could not deliver the OTP.") from exc


def send_sms_otp(phone_number, code):
    provider = settings.SMS_PROVIDER
    if provider == "console":
        if not settings.SMS_CONSOLE_ALLOWED:
            raise ImproperlyConfigured(
                "The console SMS provider is disabled outside explicit development "
                "or test configuration."
            )
        raise SMSDeliveryError(
            "The console SMS provider does not deliver verification codes."
        )
    if provider == "kavenegar":
        return _send_kavenegar_otp(phone_number, code)

    raise ImproperlyConfigured(
        f"Unsupported SMS_PROVIDER '{provider}'. Use 'console' or 'kavenegar'."
    )


class OTPPolicyError(RuntimeError):
    pass


class RegistrationUnavailable(OTPPolicyError):
    pass


class OTPDeliveryUnavailable(OTPPolicyError):
    pass


class OTPRateLimited(OTPPolicyError):
    def __init__(self, retry_after):
        super().__init__("OTP issuance is temporarily unavailable.")
        self.retry_after = max(1, int(retry_after))


class VerificationStatus(Enum):
    VERIFIED = "verified"
    INVALID = "invalid"


@dataclass(frozen=True)
class VerificationResult:
    status: VerificationStatus
    user: User | None = None


def _seconds_remaining(moment):
    return max(1, int((moment - timezone.now()).total_seconds()) + 1)


def _get_or_create_pending_user(phone_number):
    User.objects.get_or_create(
        phone_number=phone_number,
        defaults={
            "first_name": "",
            "last_name": "",
            "email": "",
            "password": make_password(None),
            "is_active": False,
            "is_phone_verified": False,
        },
    )


def _snapshot_from_registration_data(registration_data):
    return {
        "pending_first_name": registration_data["first_name"],
        "pending_last_name": registration_data["last_name"],
        "pending_email": registration_data.get("email", ""),
        "pending_password_hash": make_password(registration_data["password"]),
    }


def _latest_registration_snapshot(user):
    source = (
        PhoneOTP.objects.filter(
            user=user,
            phone_number=user.phone_number,
            purpose=PhoneOTP.Purpose.REGISTER,
        )
        .exclude(pending_password_hash="")
        .order_by("-created_at", "-pk")
        .first()
    )
    if source is None:
        raise RegistrationUnavailable("A pending registration is required.")
    return {
        "pending_first_name": source.pending_first_name,
        "pending_last_name": source.pending_last_name,
        "pending_email": source.pending_email,
        "pending_password_hash": source.pending_password_hash,
    }


def _prepare_registration_otp(phone_number, registration_data=None):
    if registration_data:
        _get_or_create_pending_user(phone_number)

    with transaction.atomic():
        try:
            user = User.objects.select_for_update().get(phone_number=phone_number)
        except User.DoesNotExist as exc:
            raise RegistrationUnavailable(
                "A pending registration is required."
            ) from exc

        if user.is_phone_verified:
            raise RegistrationUnavailable("Registration cannot update this account.")

        now = timezone.now()
        window_start = now - timedelta(seconds=settings.OTP_SEND_WINDOW_SECONDS)
        recent_otps = PhoneOTP.objects.filter(
            phone_number=phone_number,
            purpose=PhoneOTP.Purpose.REGISTER,
            created_at__gte=window_start,
        )
        if recent_otps.count() >= settings.OTP_MAX_SENDS_PER_WINDOW:
            oldest = recent_otps.order_by("created_at").first()
            retry_at = oldest.created_at + timedelta(
                seconds=settings.OTP_SEND_WINDOW_SECONDS
            )
            raise OTPRateLimited(_seconds_remaining(retry_at))

        latest = recent_otps.order_by("-created_at", "-pk").first()
        if latest:
            retry_at = latest.created_at + timedelta(
                seconds=settings.OTP_RESEND_COOLDOWN_SECONDS
            )
            if retry_at > now:
                raise OTPRateLimited(_seconds_remaining(retry_at))

        snapshot = (
            _snapshot_from_registration_data(registration_data)
            if registration_data
            else _latest_registration_snapshot(user)
        )
        code = generate_otp_code()
        otp = PhoneOTP.objects.create(
            user=user,
            phone_number=phone_number,
            code_hash=make_password(code),
            expires_at=now + timedelta(seconds=settings.OTP_EXPIRY_SECONDS),
            **snapshot,
        )
        return otp.pk, code


def _complete_otp_delivery(phone_number, otp_id, delivery_status):
    with transaction.atomic():
        user = (
            User.objects.select_for_update().filter(phone_number=phone_number).first()
        )
        if user is None:
            return False

        otp = (
            PhoneOTP.objects.select_for_update()
            .filter(
                pk=otp_id,
                user=user,
                phone_number=phone_number,
                purpose=PhoneOTP.Purpose.REGISTER,
            )
            .first()
        )
        if otp is None or otp.delivery_status != PhoneOTP.DeliveryStatus.PENDING:
            return False

        now = timezone.now()
        if delivery_status != PhoneOTP.DeliveryStatus.SENT:
            otp.delivery_status = delivery_status
            otp.invalidated_at = now
            otp.save(update_fields=("delivery_status", "invalidated_at"))
            return False

        if user.is_phone_verified:
            otp.delivery_status = PhoneOTP.DeliveryStatus.FAILED
            otp.invalidated_at = now
            otp.save(update_fields=("delivery_status", "invalidated_at"))
            return False

        if otp.invalidated_at is not None:
            otp.delivery_status = PhoneOTP.DeliveryStatus.SENT
            otp.sent_at = now
            otp.invalidated_at = otp.invalidated_at or now
            otp.save(update_fields=("delivery_status", "sent_at", "invalidated_at"))
            return False

        PhoneOTP.objects.select_for_update().filter(
            user=user,
            phone_number=phone_number,
            purpose=PhoneOTP.Purpose.REGISTER,
            is_used=False,
            invalidated_at__isnull=True,
        ).exclude(pk=otp.pk).update(invalidated_at=now)
        otp.delivery_status = PhoneOTP.DeliveryStatus.SENT
        otp.sent_at = now
        otp.expires_at = now + timedelta(seconds=settings.OTP_EXPIRY_SECONDS)
        otp.save(update_fields=("delivery_status", "sent_at", "expires_at"))
        return True


def _issue_otp(phone_number, registration_data=None):
    otp_id, code = _prepare_registration_otp(phone_number, registration_data)
    try:
        send_sms_otp(phone_number, code)
    except SMSDeliveryError:
        _complete_otp_delivery(
            phone_number,
            otp_id,
            PhoneOTP.DeliveryStatus.UNCERTAIN,
        )
        raise OTPDeliveryUnavailable("OTP delivery could not be confirmed.")
    except ImproperlyConfigured as exc:
        _complete_otp_delivery(
            phone_number,
            otp_id,
            PhoneOTP.DeliveryStatus.FAILED,
        )
        raise OTPDeliveryUnavailable("OTP delivery is unavailable.") from exc
    finally:
        code = None

    if not _complete_otp_delivery(
        phone_number,
        otp_id,
        PhoneOTP.DeliveryStatus.SENT,
    ):
        raise RegistrationUnavailable("Registration is no longer pending.")

    return settings.OTP_RESEND_COOLDOWN_SECONDS


def issue_registration_otp(phone_number, registration_data):
    return _issue_otp(phone_number, registration_data)


def resend_registration_otp(phone_number):
    return _issue_otp(phone_number)


def verify_registration_otp(phone_number, code):
    with transaction.atomic():
        user = (
            User.objects.select_for_update().filter(phone_number=phone_number).first()
        )
        if user is None or user.is_phone_verified:
            return VerificationResult(VerificationStatus.INVALID)

        otp = (
            PhoneOTP.objects.select_for_update()
            .filter(
                user=user,
                phone_number=phone_number,
                purpose=PhoneOTP.Purpose.REGISTER,
                delivery_status=PhoneOTP.DeliveryStatus.SENT,
                is_used=False,
                invalidated_at__isnull=True,
                locked_at__isnull=True,
            )
            .order_by("-sent_at", "-pk")
            .first()
        )
        if otp is None or not otp.pending_password_hash:
            return VerificationResult(VerificationStatus.INVALID)

        now = timezone.now()
        if now >= otp.expires_at:
            otp.invalidated_at = now
            otp.save(update_fields=("invalidated_at",))
            return VerificationResult(VerificationStatus.INVALID)

        if not check_password(code, otp.code_hash):
            otp.failed_attempts = min(
                otp.failed_attempts + 1,
                settings.OTP_MAX_ATTEMPTS,
            )
            update_fields = ["failed_attempts"]
            if otp.failed_attempts >= settings.OTP_MAX_ATTEMPTS:
                otp.locked_at = now
                otp.invalidated_at = now
                update_fields.extend(("locked_at", "invalidated_at"))
            otp.save(update_fields=update_fields)
            return VerificationResult(VerificationStatus.INVALID)

        otp.is_used = True
        otp.verified_at = now
        otp.save(update_fields=("is_used", "verified_at"))
        user.first_name = otp.pending_first_name
        user.last_name = otp.pending_last_name
        user.email = otp.pending_email
        user.password = otp.pending_password_hash
        user.is_phone_verified = True
        user.is_active = True
        user.save(
            update_fields=(
                "first_name",
                "last_name",
                "email",
                "password",
                "is_phone_verified",
                "is_active",
            )
        )
        return VerificationResult(VerificationStatus.VERIFIED, user=user)


def _login_identifier_hash(phone_number):
    return hmac_new(
        settings.SECRET_KEY.encode(),
        phone_number.encode(),
        sha256,
    ).hexdigest()


@dataclass(frozen=True)
class LoginResult:
    user: User | None
    retry_after: int | None = None


def authenticate_with_throttle(request, phone_number, password):
    identifier_hash = _login_identifier_hash(phone_number)
    LoginThrottle.objects.get_or_create(
        identifier_hash=identifier_hash,
        defaults={"window_started_at": timezone.now()},
    )

    with transaction.atomic():
        throttle = LoginThrottle.objects.select_for_update().get(
            identifier_hash=identifier_hash
        )
        now = timezone.now()
        if throttle.blocked_until and throttle.blocked_until > now:
            return LoginResult(None, _seconds_remaining(throttle.blocked_until))

        window_delta = timedelta(seconds=settings.LOGIN_FAILURE_WINDOW_SECONDS)
        if now >= throttle.window_started_at + window_delta:
            throttle.failed_attempts = 0
            throttle.window_started_at = now
            throttle.blocked_until = None

        user = authenticate(
            request=request,
            phone_number=phone_number,
            password=password,
        )
        if user is not None and user.is_active and user.is_phone_verified:
            throttle.delete()
            return LoginResult(user)

        throttle.failed_attempts += 1
        if throttle.failed_attempts >= settings.LOGIN_MAX_ATTEMPTS:
            throttle.blocked_until = now + timedelta(
                seconds=settings.LOGIN_BLOCK_SECONDS
            )
        throttle.save(
            update_fields=(
                "failed_attempts",
                "window_started_at",
                "blocked_until",
                "updated_at",
            )
        )
        retry_after = (
            _seconds_remaining(throttle.blocked_until)
            if throttle.blocked_until
            else None
        )
        return LoginResult(None, retry_after)
