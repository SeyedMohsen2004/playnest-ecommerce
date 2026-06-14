from django.urls import path

from accounts.views import LoginView, MeView, RegisterView, VerifyRegistrationView

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("register/verify/", VerifyRegistrationView.as_view(), name="register-verify"),
    path("login/", LoginView.as_view(), name="login"),
    path("me/", MeView.as_view(), name="me"),
]
