import logging
import secrets

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

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

    from kavenegar import KavenegarAPI

    api = KavenegarAPI(settings.KAVENEGAR_API_KEY)
    try:
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
                "message": f"PlayNest verification code: {code}",
            }
        )
    except Exception as exc:
        logger.error("Kavenegar failed to deliver an OTP.")
        raise SMSDeliveryError("The SMS provider could not deliver the OTP.") from exc


def send_sms_otp(phone_number, code):
    provider = settings.SMS_PROVIDER
    if provider == "console":
        print(f"PlayNest OTP for {phone_number}: {code}")
        return None
    if provider == "kavenegar":
        return _send_kavenegar_otp(phone_number, code)

    raise ImproperlyConfigured(
        f"Unsupported SMS_PROVIDER '{provider}'. Use 'console' or 'kavenegar'."
    )
