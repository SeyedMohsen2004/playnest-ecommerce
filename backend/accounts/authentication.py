from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class VerifiedUserJWTAuthentication(JWTAuthentication):
    """Accept bearer tokens only for active, phone-verified users."""

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if not user.is_phone_verified:
            raise AuthenticationFailed(
                "User is not eligible for authentication.",
                code="user_not_verified",
            )
        return user


class VerifiedUserJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    """Describe the custom verified-user JWT authenticator in OpenAPI."""

    target_class = VerifiedUserJWTAuthentication
    name = "jwtAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
