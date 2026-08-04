from django.urls import path

from accounts.views import (
    CSRFTokenView,
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
    ResendRegistrationView,
    VerifyRegistrationView,
)

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("register/verify/", VerifyRegistrationView.as_view(), name="register-verify"),
    path("register/resend/", ResendRegistrationView.as_view(), name="register-resend"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("csrf/", CSRFTokenView.as_view(), name="csrf"),
    path("me/", MeView.as_view(), name="me"),
]
