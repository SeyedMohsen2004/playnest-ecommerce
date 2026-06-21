from unittest.mock import patch

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from django.urls import reverse

from accounts.models import PhoneOTP, User
from accounts.services import send_sms_otp

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


@override_settings(SMS_PROVIDER="console")
def test_console_sms_provider_prints_without_external_api(capsys):
    send_sms_otp(PHONE_NUMBER, "123456")

    output = capsys.readouterr().out
    assert PHONE_NUMBER in output
    assert "123456" in output


@override_settings(
    SMS_PROVIDER="kavenegar",
    KAVENEGAR_API_KEY="",
    KAVENEGAR_SENDER="10004346",
    KAVENEGAR_VERIFY_TEMPLATE="",
)
def test_kavenegar_sms_provider_requires_api_key():
    with pytest.raises(ImproperlyConfigured, match="KAVENEGAR_API_KEY"):
        send_sms_otp(PHONE_NUMBER, "123456")


@override_settings(
    SMS_PROVIDER="kavenegar",
    KAVENEGAR_API_KEY="test-api-key",
    KAVENEGAR_SENDER="",
    KAVENEGAR_VERIFY_TEMPLATE="playnest-otp",
)
@patch("kavenegar.KavenegarAPI")
def test_kavenegar_template_delivery_is_mocked(kavenegar_api):
    send_sms_otp(PHONE_NUMBER, "123456")

    kavenegar_api.assert_called_once_with("test-api-key")
    kavenegar_api.return_value.verify_lookup.assert_called_once_with(
        {
            "receptor": PHONE_NUMBER,
            "token": "123456",
            "template": "playnest-otp",
        }
    )


@override_settings(
    SMS_PROVIDER="kavenegar",
    KAVENEGAR_API_KEY="test-api-key",
    KAVENEGAR_SENDER="10004346",
    KAVENEGAR_VERIFY_TEMPLATE="",
)
@patch("kavenegar.KavenegarAPI")
def test_kavenegar_regular_sms_delivery_is_mocked(kavenegar_api):
    send_sms_otp(PHONE_NUMBER, "123456")

    kavenegar_api.return_value.sms_send.assert_called_once_with(
        {
            "sender": "10004346",
            "receptor": PHONE_NUMBER,
            "message": "IpakToys verification code: 123456",
        }
    )


@override_settings(SMS_PROVIDER="console")
def test_registration_response_does_not_expose_otp(client):
    response = client.post(
        reverse("accounts:register"),
        registration_payload(),
        content_type="application/json",
    )
    otp = PhoneOTP.objects.get(phone_number=PHONE_NUMBER)

    assert response.status_code == 201
    assert otp.code not in response.content.decode()


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
