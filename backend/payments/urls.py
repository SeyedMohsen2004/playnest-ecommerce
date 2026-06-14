from django.urls import path

from payments.views import MockGatewayView, PaymentRequestView, PaymentVerifyView

app_name = "payments"

urlpatterns = [
    path("request/", PaymentRequestView.as_view(), name="request"),
    path("verify/", PaymentVerifyView.as_view(), name="verify"),
    path("mock-gateway/", MockGatewayView.as_view(), name="mock-gateway"),
]
