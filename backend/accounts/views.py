from django.conf import settings
from django.contrib.auth import get_user_model
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.serializers import (
    AccessTokenResponseSerializer,
    AuthResponseSerializer,
    CSRFTokenResponseSerializer,
    ErrorResponseSerializer,
    LoginSerializer,
    MessageSerializer,
    PendingRegistrationResponseSerializer,
    RegisterSerializer,
    ResendRegistrationSerializer,
    UserSerializer,
    VerifyRegistrationSerializer,
)
from accounts.services import (
    OTPDeliveryUnavailable,
    OTPRateLimited,
    RegistrationUnavailable,
    VerificationStatus,
    authenticate_with_throttle,
    issue_registration_otp,
    resend_registration_otp,
    verify_registration_otp,
)

GENERIC_AUTH_ERROR = "Invalid phone number or password."
GENERIC_OTP_ERROR = "Invalid or expired verification code."


def _refresh_cookie_options():
    return {
        "path": settings.REFRESH_COOKIE_PATH,
        "secure": settings.REFRESH_COOKIE_SECURE,
        "httponly": True,
        "samesite": settings.REFRESH_COOKIE_SAMESITE,
    }


def set_refresh_cookie(response, refresh):
    response.set_cookie(
        settings.REFRESH_COOKIE_NAME,
        str(refresh),
        max_age=settings.REFRESH_TOKEN_LIFETIME_SECONDS,
        **_refresh_cookie_options(),
    )


def clear_refresh_cookie(response):
    response.set_cookie(
        settings.REFRESH_COOKIE_NAME,
        value="",
        max_age=0,
        expires="Thu, 01 Jan 1970 00:00:00 GMT",
        **_refresh_cookie_options(),
    )


def _tracked_refresh(raw_token):
    refresh = RefreshToken(raw_token)
    user = get_user_model().objects.get(pk=refresh["user_id"])
    if not user.is_active or not user.is_phone_verified:
        raise TokenError("User is not eligible for refresh.")

    outstanding = OutstandingToken.objects.filter(
        jti=refresh["jti"],
        user=user,
        token=raw_token,
    ).first()
    if outstanding is None:
        raise TokenError("Refresh session is not tracked.")
    return refresh, user, outstanding


def authenticated_response(user):
    if not user.is_active or not user.is_phone_verified:
        raise ValueError("Tokens may only be issued for verified active users.")
    refresh = RefreshToken.for_user(user)
    response = Response(
        {
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data,
        }
    )
    set_refresh_cookie(response, refresh)
    return response


@method_decorator(csrf_protect, name="dispatch")
class RegisterView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        request=RegisterSerializer,
        responses={
            202: PendingRegistrationResponseSerializer,
            400: ErrorResponseSerializer,
            429: ErrorResponseSerializer,
            503: ErrorResponseSerializer,
        },
        description=(
            "Creates or safely updates a pending registration and sends an OTP. "
            "No JWT is issued until verification succeeds. Requires a valid CSRF "
            "cookie/header pair."
        ),
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        data.pop("password_confirm", None)
        try:
            retry_after = issue_registration_otp(data["phone_number"], data)
        except RegistrationUnavailable:
            return Response(
                {
                    "message": "Registration is pending phone verification.",
                    "retry_after": settings.OTP_RESEND_COOLDOWN_SECONDS,
                },
                status=status.HTTP_202_ACCEPTED,
            )
        except OTPRateLimited as exc:
            return Response(
                {
                    "detail": "Please wait before requesting another code.",
                    "retry_after": exc.retry_after,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except OTPDeliveryUnavailable:
            return Response(
                {"detail": "Verification delivery is temporarily unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "message": "Registration is pending phone verification.",
                "retry_after": retry_after,
            },
            status=status.HTTP_202_ACCEPTED,
        )


@method_decorator(csrf_protect, name="dispatch")
class VerifyRegistrationView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        request=VerifyRegistrationSerializer,
        responses={200: AuthResponseSerializer, 400: ErrorResponseSerializer},
        description=(
            "Consumes the latest eligible delivered registration OTP, activates the "
            "account, returns an access token, and sets the refresh token only in an "
            "HttpOnly cookie. Requires CSRF protection."
        ),
    )
    def post(self, request):
        serializer = VerifyRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = verify_registration_otp(**serializer.validated_data)
        if result.status is not VerificationStatus.VERIFIED:
            raise serializers.ValidationError({"code": GENERIC_OTP_ERROR})
        return authenticated_response(result.user)


@method_decorator(csrf_protect, name="dispatch")
class ResendRegistrationView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        request=ResendRegistrationSerializer,
        responses={
            202: PendingRegistrationResponseSerializer,
            400: ErrorResponseSerializer,
            429: ErrorResponseSerializer,
            503: ErrorResponseSerializer,
        },
        description=(
            "Requests a replacement OTP for an existing pending registration. "
            "Cooldown and send-window limits are database-backed."
        ),
    )
    def post(self, request):
        serializer = ResendRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            retry_after = resend_registration_otp(
                serializer.validated_data["phone_number"]
            )
        except RegistrationUnavailable:
            return Response(
                {
                    "message": "If the registration is eligible, a code was sent.",
                    "retry_after": settings.OTP_RESEND_COOLDOWN_SECONDS,
                },
                status=status.HTTP_202_ACCEPTED,
            )
        except OTPRateLimited as exc:
            return Response(
                {
                    "detail": "Please wait before requesting another code.",
                    "retry_after": exc.retry_after,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except OTPDeliveryUnavailable:
            return Response(
                {"detail": "Verification delivery is temporarily unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "message": "If the registration is eligible, a code was sent.",
                "retry_after": retry_after,
            },
            status=status.HTTP_202_ACCEPTED,
        )


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: AuthResponseSerializer,
            400: ErrorResponseSerializer,
            429: ErrorResponseSerializer,
        },
        description=(
            "Authenticates a verified active account. The response contains an access "
            "token only; the refresh token is set as an HttpOnly cookie."
        ),
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = authenticate_with_throttle(
            request,
            serializer.validated_data["phone_number"],
            serializer.validated_data["password"],
        )
        if result.user is None:
            response_status = (
                status.HTTP_429_TOO_MANY_REQUESTS
                if result.retry_after
                else status.HTTP_400_BAD_REQUEST
            )
            body = {"detail": GENERIC_AUTH_ERROR}
            if result.retry_after:
                body["retry_after"] = result.retry_after
            return Response(body, status=response_status)
        return authenticated_response(result.user)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CSRFTokenView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        responses={200: CSRFTokenResponseSerializer},
        description=(
            "Bootstraps the CSRF cookie and returns the matching token for the "
            "X-CSRFToken header."
        ),
    )
    def get(self, request):
        return Response({"csrf_token": get_token(request)})


@method_decorator(csrf_protect, name="dispatch")
class CookieTokenRefreshView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        request=None,
        responses={
            200: AccessTokenResponseSerializer,
            401: ErrorResponseSerializer,
        },
        description=(
            "Reads a non-rotating refresh token only from the configured HttpOnly "
            "cookie and returns a new access token. JSON refresh tokens are ignored."
        ),
    )
    def post(self, request):
        raw_token = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
        if not raw_token:
            response = Response(
                {"detail": "Authentication session is unavailable."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            clear_refresh_cookie(response)
            return response
        try:
            refresh, _user, _outstanding = _tracked_refresh(raw_token)
        except (TokenError, get_user_model().DoesNotExist, KeyError, TypeError):
            response = Response(
                {"detail": "Authentication session is unavailable."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            clear_refresh_cookie(response)
            return response
        return Response({"access": str(refresh.access_token)})


@method_decorator(csrf_protect, name="dispatch")
class LogoutView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        request=None,
        responses={200: MessageSerializer},
        description=(
            "Blacklists the refresh session when present and always clears the "
            "HttpOnly refresh cookie. The operation is idempotent."
        ),
    )
    def post(self, request):
        raw_token = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
        if raw_token:
            try:
                _refresh, _user, outstanding = _tracked_refresh(raw_token)
            except (TokenError, get_user_model().DoesNotExist, KeyError, TypeError):
                pass
            else:
                BlacklistedToken.objects.get_or_create(token=outstanding)
        response = Response({"message": "Signed out."})
        clear_refresh_cookie(response)
        return response


class LegacyTokenObtainView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        request=None,
        responses={
            410: OpenApiResponse(
                description="Direct JWT token issuance is permanently disabled."
            )
        },
    )
    def post(self, request):
        return Response(
            {"detail": "This token endpoint is no longer available."},
            status=status.HTTP_410_GONE,
        )


class MeView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(responses={200: UserSerializer})
    def get(self, request):
        return Response(UserSerializer(request.user).data)
