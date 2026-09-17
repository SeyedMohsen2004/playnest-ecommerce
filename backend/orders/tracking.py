from django.core.exceptions import ValidationError

POSTAL_TRACKING_MAX_LENGTH = 100


def normalize_postal_tracking_code(value, *, required=False):
    code = value.strip()
    if (value and not code) or (required and not code):
        raise ValidationError("لطفاً کد رهگیری پستی را وارد کنید.")
    if len(code) > POSTAL_TRACKING_MAX_LENGTH:
        raise ValidationError("کد رهگیری پستی نباید بیش از ۱۰۰ نویسه باشد.")
    return code
