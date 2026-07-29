from datetime import timedelta
from pathlib import Path

from decouple import Csv, config
from django.core.exceptions import ImproperlyConfigured


def explicit_bool_config(name, *, default):
    value = str(config(name, default="true" if default else "false")).strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise ImproperlyConfigured(
        f"{name} must be an explicit boolean: true/false, yes/no, on/off, or 1/0."
    )


def csv_config(name, *, default=""):
    return [
        value
        for value in config(name, default=default, cast=Csv())
        if str(value).strip()
    ]


BASE_DIR = Path(__file__).resolve().parent.parent

DEVELOPMENT_SECRET_KEY = "unsafe-development-key-change-me"
DEBUG = explicit_bool_config("DJANGO_DEBUG", default=False)
SECRET_KEY = str(
    config(
        "DJANGO_SECRET_KEY",
        default=DEVELOPMENT_SECRET_KEY if DEBUG else "",
    )
).strip()
if not SECRET_KEY or (not DEBUG and SECRET_KEY == DEVELOPMENT_SECRET_KEY):
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY must be set to a non-default value when DEBUG is false."
    )

ALLOWED_HOSTS = csv_config(
    "DJANGO_ALLOWED_HOSTS",
    default="localhost,127.0.0.1" if DEBUG else "",
)
if not DEBUG:
    if not ALLOWED_HOSTS:
        raise ImproperlyConfigured(
            "DJANGO_ALLOWED_HOSTS must contain at least one host when DEBUG is false."
        )
    if "*" in ALLOWED_HOSTS:
        raise ImproperlyConfigured(
            "DJANGO_ALLOWED_HOSTS cannot contain a wildcard when DEBUG is false."
        )

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "django_filters",
    "rest_framework",
    "drf_spectacular",
    "accounts",
    "products",
    "orders",
    "payments",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB", default="playnest"),
        "USER": config("POSTGRES_USER", default="playnest"),
        "PASSWORD": config("POSTGRES_PASSWORD", default="playnest"),
        "HOST": config("POSTGRES_HOST", default="db"),
        "PORT": config("POSTGRES_PORT", default="5432"),
        "CONN_MAX_AGE": 60,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        )
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
AUTH_USER_MODEL = "accounts.User"
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = csv_config(
    "CORS_ALLOWED_ORIGINS",
    default=(
        "http://localhost:3000," "http://127.0.0.1:3000," "http://192.168.42.1:3000"
        if DEBUG
        else ""
    ),
)
CSRF_TRUSTED_ORIGINS = csv_config("CSRF_TRUSTED_ORIGINS")

SMS_PROVIDER = config("SMS_PROVIDER", default="console").lower()
KAVENEGAR_API_KEY = config("KAVENEGAR_API_KEY", default="")
KAVENEGAR_SENDER = config("KAVENEGAR_SENDER", default="")
KAVENEGAR_VERIFY_TEMPLATE = config("KAVENEGAR_VERIFY_TEMPLATE", default="")
ZARINPAL_MERCHANT_ID = config("ZARINPAL_MERCHANT_ID", default="")
ZARINPAL_SANDBOX = explicit_bool_config("ZARINPAL_SANDBOX", default=True)
ZARINPAL_CALLBACK_URL = config("ZARINPAL_CALLBACK_URL", default="").strip() or (
    "http://127.0.0.1:8000/api/v1/payments/zarinpal/callback/"
    if DEBUG
    else "https://ipaktoys.ir/api/v1/payments/zarinpal/callback/"
)
FRONTEND_BASE_URL = config("FRONTEND_BASE_URL", default="").strip() or (
    "http://localhost:3000" if DEBUG else "https://ipaktoys.ir"
)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "IpakToys API",
    "DESCRIPTION": (
        "Backend API for the IpakToys board game and creative games ecommerce "
        "platform."
    ),
    "VERSION": "1.0.0",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

SECURE_SSL_REDIRECT = explicit_bool_config(
    "DJANGO_SECURE_SSL_REDIRECT",
    default=False,
)
SECURE_HSTS_SECONDS = config("DJANGO_SECURE_HSTS_SECONDS", default=0, cast=int)
if SECURE_HSTS_SECONDS < 0:
    raise ImproperlyConfigured("DJANGO_SECURE_HSTS_SECONDS cannot be negative.")
SECURE_HSTS_INCLUDE_SUBDOMAINS = explicit_bool_config(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS",
    default=False,
)
SECURE_HSTS_PRELOAD = explicit_bool_config(
    "DJANGO_SECURE_HSTS_PRELOAD",
    default=False,
)
SECURE_CONTENT_TYPE_NOSNIFF = explicit_bool_config(
    "DJANGO_SECURE_CONTENT_TYPE_NOSNIFF",
    default=True,
)
SECURE_REFERRER_POLICY = str(
    config("DJANGO_SECURE_REFERRER_POLICY", default="same-origin")
).strip()
VALID_REFERRER_POLICIES = {
    "no-referrer",
    "no-referrer-when-downgrade",
    "origin",
    "origin-when-cross-origin",
    "same-origin",
    "strict-origin",
    "strict-origin-when-cross-origin",
    "unsafe-url",
}
if SECURE_REFERRER_POLICY not in VALID_REFERRER_POLICIES:
    raise ImproperlyConfigured(
        "DJANGO_SECURE_REFERRER_POLICY must be a valid Referrer-Policy value."
    )

TRUST_X_FORWARDED_PROTO = explicit_bool_config(
    "DJANGO_TRUST_X_FORWARDED_PROTO",
    default=False,
)
SECURE_PROXY_SSL_HEADER = (
    ("HTTP_X_FORWARDED_PROTO", "https") if TRUST_X_FORWARDED_PROTO else None
)
SESSION_COOKIE_SECURE = explicit_bool_config(
    "DJANGO_SESSION_COOKIE_SECURE",
    default=not DEBUG,
)
CSRF_COOKIE_SECURE = explicit_bool_config(
    "DJANGO_CSRF_COOKIE_SECURE",
    default=not DEBUG,
)
