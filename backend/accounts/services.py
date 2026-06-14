import logging
import secrets

from django.conf import settings

logger = logging.getLogger(__name__)


def generate_otp_code():
    return f"{secrets.randbelow(1_000_000):06d}"


def send_sms_otp(phone_number, code):
    if settings.DEBUG:
        print(f"PlayNest OTP for {phone_number}: {code}")
        return

    logger.warning(
        "SMS provider is not configured; OTP for phone ending in %s was not sent.",
        phone_number[-4:],
    )
