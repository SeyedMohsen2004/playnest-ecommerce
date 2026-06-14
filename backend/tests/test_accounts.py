from unittest.mock import patch

import pytest
from django.urls import reverse

from accounts.models import PhoneOTP, User

pytestmark = pytest.mark.django_db

PHONE_NUMBER = "09123456789"
PASSWORD = "StrongPassword!42"


def registration_payload():
    return {
        "phone_number": PHONE_NUMBER,
        "first_name": "Play",
        "last_name": "Tester",
        "email": "tester@example.com",
        "password": PASSWORD,
        "password_confirm": PASSWORD,
    }


@patch("accounts.views.send_sms_otp")
def test_register_sends_otp(send_sms_otp, client):
    response = client.post(
        reverse("accounts:register"),
        registration_payload(),
        content_type="application/json",
    )

    assert response.status_code == 201
    assert response.json() == {"message": "Verification code sent."}
    user = User.objects.get(phone_number=PHONE_NUMBER)
    otp = PhoneOTP.objects.get(phone_number=PHONE_NUMBER)
    assert user.is_active is False
    assert user.is_phone_verified is False
    assert len(otp.code) == 6
    assert otp.code.isdigit()
    send_sms_otp.assert_called_once_with(PHONE_NUMBER, otp.code)


def test_verify_otp_activates_user_and_returns_tokens(client):
    user = User.objects.create_user(
        phone_number=PHONE_NUMBER,
        password=PASSWORD,
        first_name="Play",
        last_name="Tester",
    )
    otp = PhoneOTP.objects.create(
        phone_number=PHONE_NUMBER,
        code="123456",
        expires_at=PhoneOTP.expiration_time(),
    )

    response = client.post(
        reverse("accounts:register-verify"),
        {"phone_number": PHONE_NUMBER, "code": otp.code},
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json()["access"]
    assert response.json()["refresh"]
    assert response.json()["user"]["phone_number"] == PHONE_NUMBER
    user.refresh_from_db()
    otp.refresh_from_db()
    assert user.is_active is True
    assert user.is_phone_verified is True
    assert otp.is_used is True
    assert otp.verified_at is not None


def test_login_with_phone_number_and_password_returns_tokens(client):
    User.objects.create_user(
        phone_number=PHONE_NUMBER,
        password=PASSWORD,
        first_name="Play",
        last_name="Tester",
        is_active=True,
        is_phone_verified=True,
    )

    response = client.post(
        reverse("accounts:login"),
        {"phone_number": PHONE_NUMBER, "password": PASSWORD},
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json()["access"]
    assert response.json()["refresh"]
    assert response.json()["user"]["phone_number"] == PHONE_NUMBER


def test_unverified_user_cannot_login(client):
    User.objects.create_user(
        phone_number=PHONE_NUMBER,
        password=PASSWORD,
        first_name="Play",
        last_name="Tester",
        is_active=True,
        is_phone_verified=False,
    )

    response = client.post(
        reverse("accounts:login"),
        {"phone_number": PHONE_NUMBER, "password": PASSWORD},
        content_type="application/json",
    )

    assert response.status_code == 400


def test_me_requires_authentication_and_returns_user(client):
    user = User.objects.create_user(
        phone_number=PHONE_NUMBER,
        password=PASSWORD,
        first_name="Play",
        last_name="Tester",
        is_active=True,
        is_phone_verified=True,
    )

    unauthorized_response = client.get(reverse("accounts:me"))

    login_response = client.post(
        reverse("accounts:login"),
        {"phone_number": PHONE_NUMBER, "password": PASSWORD},
        content_type="application/json",
    )
    access = login_response.json()["access"]
    authenticated_response = client.get(
        reverse("accounts:me"),
        HTTP_AUTHORIZATION=f"Bearer {access}",
    )

    assert unauthorized_response.status_code == 401
    assert authenticated_response.status_code == 200
    assert authenticated_response.json()["id"] == user.id
    assert authenticated_response.json()["phone_number"] == PHONE_NUMBER
