from django.urls import path

from payments.views import (
    PaymentRequestView,
    PaymentVerifyView,
    ZarinPalCallbackView,
)

app_name = "payments"

urlpatterns = [
    path("request/", PaymentRequestView.as_view(), name="request"),
    path("verify/", PaymentVerifyView.as_view(), name="verify"),
    path(
        "zarinpal/callback/",
        ZarinPalCallbackView.as_view(),
        name="zarinpal-callback",
    ),
]
