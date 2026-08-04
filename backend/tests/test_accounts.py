from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch

import pytest
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.db import close_old_connections, connections
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import LoginThrottle, PhoneOTP, User
from accounts.services import (
    OTPRateLimited,
    RegistrationUnavailable,
    _complete_otp_delivery,
    _prepare_registration_otp,
    SMSDeliveryError,
    VerificationStatus,
    resend_registration_otp,
    send_sms_otp,
    verify_registration_otp,
)

pytestmark = pytest.mark.django_db

PHONE_NUMBER = "09123456789"
OTHER_PHONE_NUMBER = "09987654321"
PASSWORD = "StrongPassword!42"
OTP_CODE = "123456"


def registration_payload(phone_number=PHONE_NUMBER):
    return {
        "phone_number": phone_number,
        "first_name": "Play",
        "last_name": "Tester",
        "email": "tester@example.com",
        "password": PASSWORD,
        "password_confirm": PASSWORD,
    }


def create_user(*, verified=False, phone_number=PHONE_NUMBER):
    return User.objects.create_user(
        phone_number=phone_number,
        password=PASSWORD,
        first_name="Play",
        last_name="Tester",
        is_active=verified,
        is_phone_verified=verified,
    )


def create_sent_otp(*, user=None, code=OTP_CODE, expires_at=None):
    user = user or create_user()
    now = timezone.now()
    return PhoneOTP.objects.create(
        user=user,
        phone_number=user.phone_number,
        code_hash=make_password(code),
        pending_first_name=user.first_name,
        pending_last_name=user.last_name,
        pending_email=user.email,
        pending_password_hash=user.password,
        delivery_status=PhoneOTP.DeliveryStatus.SENT,
        sent_at=now,
        expires_at=expires_at or now + timedelta(minutes=2),
    )


def register_with_mocked_delivery(client, phone_number=PHONE_NUMBER):
    with patch("accounts.services.send_sms_otp") as delivery:
        response = client.post(
            reverse("accounts:register"),
            registration_payload(phone_number),
            content_type="application/json",
        )
    return response, delivery.call_args.args[1]


def login(client, phone_number=PHONE_NUMBER, password=PASSWORD):
    return client.post(
        reverse("accounts:login"),
        {"phone_number": phone_number, "password": password},
        content_type="application/json",
    )


def test_registration_creates_pending_user_and_hashed_delivered_otp(client):
    response, code = register_with_mocked_delivery(client)

    assert response.status_code == 202
    assert "access" not in response.json()
    assert "refresh" not in response.json()
    user = User.objects.get(phone_number=PHONE_NUMBER)
    otp = PhoneOTP.objects.get(phone_number=PHONE_NUMBER)
    assert user.is_active is False
    assert user.is_phone_verified is False
    assert user.has_usable_password() is False
    assert otp.delivery_status == PhoneOTP.DeliveryStatus.SENT
    assert otp.code_hash != code
    assert check_password(code, otp.code_hash)
    with pytest.raises(FieldDoesNotExist):
        PhoneOTP._meta.get_field("code")


def test_verified_account_cannot_be_overwritten_by_registration(client):
    user = create_user(verified=True)
    old_password = user.password

    with patch("accounts.services.send_sms_otp") as delivery:
        response = client.post(
            reverse("accounts:register"),
            registration_payload(),
            content_type="application/json",
        )

    assert response.status_code == 202
    user.refresh_from_db()
    assert user.password == old_password
    assert user.is_active is True
    assert user.is_phone_verified is True
    assert not PhoneOTP.objects.filter(phone_number=PHONE_NUMBER).exists()
    delivery.assert_not_called()


def test_registration_password_mismatch_fails_before_user_creation(client):
    payload = registration_payload()
    payload["password_confirm"] = "DifferentPassword!42"
    response = client.post(
        reverse("accounts:register"), payload, content_type="application/json"
    )

    assert response.status_code == 400
    assert not User.objects.filter(phone_number=PHONE_NUMBER).exists()


@override_settings(SMS_CONSOLE_ALLOWED=True, SMS_PROVIDER="console")
def test_console_sms_adapter_never_claims_delivery_or_exposes_plaintext(capsys, caplog):
    with pytest.raises(SMSDeliveryError, match="does not deliver"):
        send_sms_otp(PHONE_NUMBER, OTP_CODE)

    assert OTP_CODE not in capsys.readouterr().out
    assert OTP_CODE not in caplog.text
    assert PHONE_NUMBER not in caplog.text


@override_settings(SMS_CONSOLE_ALLOWED=False, SMS_PROVIDER="console")
def test_console_sms_provider_fails_closed_when_not_explicitly_allowed():
    with pytest.raises(ImproperlyConfigured, match="console SMS provider"):
        send_sms_otp(PHONE_NUMBER, OTP_CODE)


@override_settings(SMS_CONSOLE_ALLOWED=True, SMS_PROVIDER="console")
def test_console_registration_returns_503_and_never_creates_an_eligible_otp(client):
    response = client.post(
        reverse("accounts:register"),
        registration_payload(),
        content_type="application/json",
    )

    assert response.status_code == 503
    otp = PhoneOTP.objects.get(phone_number=PHONE_NUMBER)
    assert otp.delivery_status == PhoneOTP.DeliveryStatus.UNCERTAIN
    assert otp.invalidated_at is not None


@override_settings(
    SMS_PROVIDER="kavenegar",
    KAVENEGAR_API_KEY="",
    KAVENEGAR_SENDER="synthetic-sender",
    KAVENEGAR_VERIFY_TEMPLATE="",
)
def test_kavenegar_sms_provider_requires_api_key():
    with pytest.raises(ImproperlyConfigured, match="KAVENEGAR_API_KEY"):
        send_sms_otp(PHONE_NUMBER, OTP_CODE)


@override_settings(
    SMS_PROVIDER="kavenegar",
    KAVENEGAR_API_KEY="synthetic-api-key",
    KAVENEGAR_SENDER="",
    KAVENEGAR_VERIFY_TEMPLATE="playnest-otp",
)
@patch("kavenegar.KavenegarAPI")
def test_kavenegar_template_delivery_is_mocked(kavenegar_api):
    send_sms_otp(PHONE_NUMBER, OTP_CODE)

    kavenegar_api.assert_called_once_with("synthetic-api-key")
    kavenegar_api.return_value.verify_lookup.assert_called_once_with(
        {
            "receptor": PHONE_NUMBER,
            "token": OTP_CODE,
            "template": "playnest-otp",
        }
    )


@patch("accounts.services.send_sms_otp", side_effect=SMSDeliveryError("unavailable"))
def test_failed_delivery_leaves_no_usable_otp(delivery, client):
    response = client.post(
        reverse("accounts:register"),
        registration_payload(),
        content_type="application/json",
    )

    assert response.status_code == 503
    otp = PhoneOTP.objects.get(phone_number=PHONE_NUMBER)
    assert otp.delivery_status == PhoneOTP.DeliveryStatus.UNCERTAIN
    assert otp.invalidated_at is not None
    assert verify_registration_otp(PHONE_NUMBER, OTP_CODE).status is (
        VerificationStatus.INVALID
    )


def test_expired_and_superseded_otps_fail():
    user = create_user()
    expired = create_sent_otp(
        user=user,
        expires_at=timezone.now() - timedelta(seconds=1),
    )
    assert verify_registration_otp(PHONE_NUMBER, OTP_CODE).status is (
        VerificationStatus.INVALID
    )
    expired.refresh_from_db()
    assert expired.invalidated_at is not None

    old = create_sent_otp(user=user, code="111111")
    old.invalidated_at = timezone.now()
    old.save(update_fields=("invalidated_at",))
    create_sent_otp(user=user, code="222222")
    assert verify_registration_otp(PHONE_NUMBER, "111111").status is (
        VerificationStatus.INVALID
    )


@override_settings(OTP_MAX_ATTEMPTS=2)
def test_invalid_attempts_commit_and_lock_before_validation_response(client):
    otp = create_sent_otp()

    first = client.post(
        reverse("accounts:register-verify"),
        {"phone_number": PHONE_NUMBER, "code": "000000"},
        content_type="application/json",
    )
    second = client.post(
        reverse("accounts:register-verify"),
        {"phone_number": PHONE_NUMBER, "code": "000001"},
        content_type="application/json",
    )

    assert first.status_code == second.status_code == 400
    otp.refresh_from_db()
    assert otp.failed_attempts == 2
    assert otp.locked_at is not None
    assert otp.invalidated_at is not None
    assert verify_registration_otp(PHONE_NUMBER, OTP_CODE).status is (
        VerificationStatus.INVALID
    )


def test_successful_verification_activates_once_and_hides_refresh(client):
    user = create_user()
    otp = create_sent_otp(user=user)

    response = client.post(
        reverse("accounts:register-verify"),
        {"phone_number": PHONE_NUMBER, "code": OTP_CODE},
        content_type="application/json",
    )
    repeated = client.post(
        reverse("accounts:register-verify"),
        {"phone_number": PHONE_NUMBER, "code": OTP_CODE},
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json()["access"]
    assert "refresh" not in response.json()
    assert settings.REFRESH_COOKIE_NAME in response.cookies
    assert repeated.status_code == 400
    user.refresh_from_db()
    otp.refresh_from_db()
    assert user.is_active and user.is_phone_verified
    assert otp.is_used and otp.verified_at is not None


@pytest.mark.django_db(transaction=True)
def test_concurrent_verification_consumes_otp_once():
    user = create_user()
    create_sent_otp(user=user)
    barrier = Barrier(2)

    def verify():
        close_old_connections()
        try:
            barrier.wait(timeout=5)
            return verify_registration_otp(PHONE_NUMBER, OTP_CODE).status
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: verify(), range(2)))

    assert results.count(VerificationStatus.VERIFIED) == 1
    assert results.count(VerificationStatus.INVALID) == 1
    assert PhoneOTP.objects.get(phone_number=PHONE_NUMBER).is_used is True


@override_settings(OTP_RESEND_COOLDOWN_SECONDS=60)
def test_resend_cooldown_is_database_backed(client):
    register_response, _ = register_with_mocked_delivery(client)
    resend_response = client.post(
        reverse("accounts:register-resend"),
        {"phone_number": PHONE_NUMBER},
        content_type="application/json",
    )

    assert register_response.status_code == 202
    assert resend_response.status_code == 429
    assert resend_response.json()["retry_after"] > 0
    assert PhoneOTP.objects.filter(phone_number=PHONE_NUMBER).count() == 1


@override_settings(
    OTP_MAX_SENDS_PER_WINDOW=2,
    OTP_RESEND_COOLDOWN_SECONDS=1,
    OTP_SEND_WINDOW_SECONDS=3600,
)
def test_send_window_limit_counts_persisted_issuance_attempts(client):
    user = create_user()
    old = timezone.now() - timedelta(minutes=2)
    for suffix in ("1", "2"):
        otp = create_sent_otp(user=user, code=f"12345{suffix}")
        PhoneOTP.objects.filter(pk=otp.pk).update(created_at=old)

    response = client.post(
        reverse("accounts:register-resend"),
        {"phone_number": PHONE_NUMBER},
        content_type="application/json",
    )
    assert response.status_code == 429


@pytest.mark.django_db(transaction=True)
@override_settings(OTP_RESEND_COOLDOWN_SECONDS=60)
def test_concurrent_resend_allows_only_one_issuance():
    user = create_user()
    original = create_sent_otp(user=user)

    PhoneOTP.objects.filter(pk=original.pk).update(
        created_at=timezone.now() - timedelta(minutes=2)
    )

    barrier = Barrier(2)

    def resend():
        close_old_connections()
        try:
            barrier.wait(timeout=5)
            return resend_registration_otp(PHONE_NUMBER)
        except OTPRateLimited:
            return "limited"
        finally:
            connections.close_all()

    with patch("accounts.services.send_sms_otp"):
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: resend(), range(2)))

    successful_results = [result for result in results if result != "limited"]

    assert len(successful_results) == 1
    assert results.count("limited") == 1

    assert PhoneOTP.objects.filter(phone_number=PHONE_NUMBER).count() == 2

    assert (
        PhoneOTP.objects.filter(
            phone_number=PHONE_NUMBER,
            delivery_status=PhoneOTP.DeliveryStatus.SENT,
            is_used=False,
            invalidated_at__isnull=True,
        ).count()
        == 1
    )

    original.refresh_from_db()
    assert original.invalidated_at is not None


@pytest.mark.django_db(transaction=True)
@override_settings(OTP_RESEND_COOLDOWN_SECONDS=1)
def test_resend_racing_verification_has_one_safe_outcome():
    user = create_user()
    original = create_sent_otp(user=user)
    PhoneOTP.objects.filter(pk=original.pk).update(
        created_at=timezone.now() - timedelta(minutes=2)
    )
    barrier = Barrier(2)

    def verify():
        close_old_connections()
        try:
            barrier.wait(timeout=5)
            return verify_registration_otp(PHONE_NUMBER, OTP_CODE).status
        finally:
            connections.close_all()

    def resend():
        close_old_connections()
        try:
            barrier.wait(timeout=5)
            try:
                resend_registration_otp(PHONE_NUMBER)
                return "resent"
            except RegistrationUnavailable:
                return "unavailable"
        finally:
            connections.close_all()

    with (
        patch("accounts.services.send_sms_otp"),
        patch("accounts.services.generate_otp_code", return_value="222222"),
    ):
        with ThreadPoolExecutor(max_workers=2) as executor:
            verification_future = executor.submit(verify)
            resend_future = executor.submit(resend)
            verification = verification_future.result()
            resend_result = resend_future.result()

    user.refresh_from_db()
    if verification is VerificationStatus.VERIFIED:
        assert user.is_active and user.is_phone_verified
        assert resend_result == "unavailable"
        assert not PhoneOTP.objects.filter(
            code_hash__isnull=False,
            delivery_status=PhoneOTP.DeliveryStatus.SENT,
            invalidated_at__isnull=True,
            is_used=False,
        ).exists()
    else:
        assert verification is VerificationStatus.INVALID
        assert resend_result == "resent"
        assert user.is_active is False
        assert (
            PhoneOTP.objects.filter(
                delivery_status=PhoneOTP.DeliveryStatus.SENT,
                invalidated_at__isnull=True,
                is_used=False,
            ).count()
            == 1
        )


def test_pending_inactive_and_unverified_users_receive_generic_login_error(client):
    create_user()
    response = login(client)

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid phone number or password."}


def test_unknown_phone_and_wrong_password_have_same_public_error(client):
    create_user(verified=True)
    unknown = login(client, OTHER_PHONE_NUMBER, "WrongPassword!42")
    wrong = login(client, PHONE_NUMBER, "WrongPassword!42")

    assert unknown.status_code == wrong.status_code == 400
    assert unknown.json() == wrong.json()


@override_settings(LOGIN_MAX_ATTEMPTS=2, LOGIN_BLOCK_SECONDS=60)
def test_login_throttle_blocks_temporarily_and_success_clears_state(client):
    create_user(verified=True)
    assert login(client, password="WrongPassword!42").status_code == 400
    blocked = login(client, password="WrongPassword!43")
    assert blocked.status_code == 429
    assert LoginThrottle.objects.get().blocked_until is not None
    assert login(client).status_code == 429

    LoginThrottle.objects.update(blocked_until=timezone.now() - timedelta(seconds=1))
    recovered = login(client)
    assert recovered.status_code == 200
    assert not LoginThrottle.objects.exists()


@override_settings(REFRESH_COOKIE_SECURE=True)
def test_login_returns_access_and_secure_httponly_refresh_cookie(client):
    create_user(verified=True)
    response = login(client)

    assert response.status_code == 200
    assert response.json()["access"]
    assert "refresh" not in response.json()
    cookie = response.cookies[settings.REFRESH_COOKIE_NAME]
    assert cookie["httponly"] is True
    assert cookie["secure"] is True
    assert cookie["samesite"] == settings.REFRESH_COOKIE_SAMESITE
    assert cookie["path"] == settings.REFRESH_COOKIE_PATH
    assert int(cookie["max-age"]) == settings.REFRESH_TOKEN_LIFETIME_SECONDS


def test_cookie_refresh_accepts_cookie_rejects_json_and_rejects_unverified(client):
    user = create_user(verified=True)
    login_response = login(client)
    refresh_response = client.post(
        reverse("token_refresh"), {}, content_type="application/json"
    )
    assert refresh_response.status_code == 200
    assert set(refresh_response.json()) == {"access"}

    no_cookie = Client()
    body_response = no_cookie.post(
        reverse("token_refresh"),
        {"refresh": str(RefreshToken.for_user(user))},
        content_type="application/json",
    )
    assert body_response.status_code == 401
    assert "refresh" not in body_response.json()

    unverified = create_user(phone_number=OTHER_PHONE_NUMBER)
    no_cookie.cookies[settings.REFRESH_COOKIE_NAME] = str(
        RefreshToken.for_user(unverified)
    )
    rejected = no_cookie.post(reverse("token_refresh"))
    assert rejected.status_code == 401
    assert rejected.cookies[settings.REFRESH_COOKIE_NAME]["max-age"] == 0
    assert login_response.cookies[settings.REFRESH_COOKIE_NAME].value


def test_logout_revokes_refresh_cookie_and_is_idempotent(client):
    create_user(verified=True)
    login_response = login(client)
    raw_refresh = login_response.cookies[settings.REFRESH_COOKIE_NAME].value

    logout_response = client.post(reverse("accounts:logout"))
    repeated = client.post(reverse("accounts:logout"))
    assert logout_response.status_code == repeated.status_code == 200
    assert logout_response.cookies[settings.REFRESH_COOKIE_NAME]["max-age"] == 0

    client.cookies[settings.REFRESH_COOKIE_NAME] = raw_refresh
    assert client.post(reverse("token_refresh")).status_code == 401


def test_untracked_refresh_token_is_rejected_and_cleared(client):
    user = create_user(verified=True)
    refresh = RefreshToken.for_user(user)
    OutstandingToken.objects.filter(jti=refresh["jti"]).delete()
    client.cookies[settings.REFRESH_COOKIE_NAME] = str(refresh)

    response = client.post(reverse("token_refresh"))

    assert response.status_code == 401
    assert response.cookies[settings.REFRESH_COOKIE_NAME]["max-age"] == 0
    assert not OutstandingToken.objects.filter(jti=refresh["jti"]).exists()


def test_active_unverified_user_cannot_use_old_access_token(client):
    user = User.objects.create_user(
        phone_number=PHONE_NUMBER,
        password=PASSWORD,
        first_name="Legacy",
        last_name="Pending",
        is_active=True,
        is_phone_verified=False,
    )
    access = str(RefreshToken.for_user(user).access_token)

    response = client.get(
        reverse("accounts:me"),
        HTTP_AUTHORIZATION=f"Bearer {access}",
    )

    assert response.status_code == 401


def test_legacy_token_obtain_never_issues_tokens_to_unverified_user(client):
    create_user()
    response = client.post(
        reverse("token_obtain_pair"),
        {"phone_number": PHONE_NUMBER, "password": PASSWORD},
        content_type="application/json",
    )
    assert response.status_code == 410
    assert "access" not in response.json()
    assert "refresh" not in response.json()


@override_settings(
    CSRF_TRUSTED_ORIGINS=["http://localhost:3000"],
    OTP_RESEND_COOLDOWN_SECONDS=1,
)
def test_all_cookie_auth_mutations_require_realistic_csrf_origin_and_header():
    trusted_origin = "http://localhost:3000"
    untrusted_origin = "https://attacker.example"
    csrf_client = Client(enforce_csrf_checks=True)
    bootstrap = csrf_client.get(reverse("accounts:csrf"))
    csrf_token = bootstrap.json()["csrf_token"]

    register_payload = registration_payload(OTHER_PHONE_NUMBER)
    with (
        patch("accounts.services.generate_otp_code", return_value=OTP_CODE),
        patch("accounts.services.send_sms_otp"),
    ):
        assert (
            csrf_client.post(
                reverse("accounts:register"),
                register_payload,
                content_type="application/json",
                HTTP_ORIGIN=trusted_origin,
            ).status_code
            == 403
        )
        assert (
            csrf_client.post(
                reverse("accounts:register"),
                register_payload,
                content_type="application/json",
                HTTP_ORIGIN=untrusted_origin,
                HTTP_X_CSRFTOKEN=csrf_token,
            ).status_code
            == 403
        )
        registered = csrf_client.post(
            reverse("accounts:register"),
            register_payload,
            content_type="application/json",
            HTTP_ORIGIN=trusted_origin,
            HTTP_X_CSRFTOKEN=csrf_token,
        )
    assert registered.status_code == 202

    PhoneOTP.objects.filter(phone_number=OTHER_PHONE_NUMBER).update(
        created_at=timezone.now() - timedelta(minutes=2)
    )
    assert (
        csrf_client.post(
            reverse("accounts:register-resend"),
            {"phone_number": OTHER_PHONE_NUMBER},
            content_type="application/json",
            HTTP_ORIGIN=trusted_origin,
        ).status_code
        == 403
    )
    with patch("accounts.services.send_sms_otp"):
        resent = csrf_client.post(
            reverse("accounts:register-resend"),
            {"phone_number": OTHER_PHONE_NUMBER},
            content_type="application/json",
            HTTP_ORIGIN=trusted_origin,
            HTTP_X_CSRFTOKEN=csrf_token,
        )
    assert resent.status_code == 202

    assert (
        csrf_client.post(
            reverse("accounts:register-verify"),
            {"phone_number": OTHER_PHONE_NUMBER, "code": OTP_CODE},
            content_type="application/json",
            HTTP_ORIGIN=trusted_origin,
        ).status_code
        == 403
    )

    latest = PhoneOTP.objects.filter(phone_number=OTHER_PHONE_NUMBER).latest("pk")
    latest.code_hash = make_password(OTP_CODE)
    latest.save(update_fields=("code_hash",))
    verified = csrf_client.post(
        reverse("accounts:register-verify"),
        {"phone_number": OTHER_PHONE_NUMBER, "code": OTP_CODE},
        content_type="application/json",
        HTTP_ORIGIN=trusted_origin,
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert verified.status_code == 200

    create_user(verified=True)
    assert (
        csrf_client.post(
            reverse("accounts:login"),
            {"phone_number": PHONE_NUMBER, "password": PASSWORD},
            content_type="application/json",
            HTTP_ORIGIN=trusted_origin,
        ).status_code
        == 403
    )
    authenticated = csrf_client.post(
        reverse("accounts:login"),
        {"phone_number": PHONE_NUMBER, "password": PASSWORD},
        content_type="application/json",
        HTTP_ORIGIN=trusted_origin,
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert authenticated.status_code == 200

    assert (
        csrf_client.post(
            reverse("token_refresh"),
            HTTP_ORIGIN=trusted_origin,
        ).status_code
        == 403
    )
    refreshed = csrf_client.post(
        reverse("token_refresh"),
        HTTP_ORIGIN=trusted_origin,
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert refreshed.status_code == 200

    assert (
        csrf_client.post(
            reverse("accounts:logout"),
            HTTP_ORIGIN=trusted_origin,
        ).status_code
        == 403
    )
    logged_out = csrf_client.post(
        reverse("accounts:logout"),
        HTTP_ORIGIN=trusted_origin,
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert logged_out.status_code == 200


def test_auth_responses_and_logs_do_not_expose_sensitive_values(client, caplog):
    with patch("accounts.services.send_sms_otp") as delivery:
        response = client.post(
            reverse("accounts:register"),
            registration_payload(),
            content_type="application/json",
        )
    otp_code = delivery.call_args.args[1]
    serialized = response.content.decode()
    assert PASSWORD not in serialized
    assert otp_code not in serialized
    assert PASSWORD not in caplog.text
    assert otp_code not in caplog.text


def test_me_requires_authentication_and_returns_verified_user(client):
    user = create_user(verified=True)
    assert client.get(reverse("accounts:me")).status_code == 401
    access = login(client).json()["access"]
    response = client.get(reverse("accounts:me"), HTTP_AUTHORIZATION=f"Bearer {access}")
    assert response.status_code == 200
    assert response.json()["id"] == user.id


@override_settings(OTP_RESEND_COOLDOWN_SECONDS=1)
def test_failed_new_delivery_cannot_change_payload_authorized_by_old_otp(client):
    payload_a = registration_payload()
    payload_a.update(first_name="PayloadA", last_name="Original")
    with (
        patch("accounts.services.generate_otp_code", return_value="111111"),
        patch("accounts.services.send_sms_otp"),
    ):
        first = client.post(
            reverse("accounts:register"),
            payload_a,
            content_type="application/json",
        )
    assert first.status_code == 202
    PhoneOTP.objects.update(created_at=timezone.now() - timedelta(minutes=2))

    payload_b = registration_payload()
    payload_b.update(
        first_name="PayloadB",
        last_name="Replacement",
        password="DifferentStrongPassword!42",
        password_confirm="DifferentStrongPassword!42",
    )
    with (
        patch("accounts.services.generate_otp_code", return_value="222222"),
        patch(
            "accounts.services.send_sms_otp",
            side_effect=SMSDeliveryError("unavailable"),
        ),
    ):
        second = client.post(
            reverse("accounts:register"),
            payload_b,
            content_type="application/json",
        )
    assert second.status_code == 503

    result = verify_registration_otp(PHONE_NUMBER, "111111")
    assert result.status is VerificationStatus.VERIFIED
    user = User.objects.get(phone_number=PHONE_NUMBER)
    assert user.first_name == "PayloadA"
    assert user.last_name == "Original"
    assert user.check_password(PASSWORD)
    assert not user.check_password("DifferentStrongPassword!42")


@override_settings(OTP_RESEND_COOLDOWN_SECONDS=1)
def test_successfully_delivered_new_payload_invalidates_old_otp(client):
    payload_a = registration_payload()
    payload_a.update(first_name="PayloadA")
    with (
        patch("accounts.services.generate_otp_code", return_value="111111"),
        patch("accounts.services.send_sms_otp"),
    ):
        assert (
            client.post(
                reverse("accounts:register"),
                payload_a,
                content_type="application/json",
            ).status_code
            == 202
        )
    PhoneOTP.objects.update(created_at=timezone.now() - timedelta(minutes=2))

    payload_b = registration_payload()
    payload_b.update(
        first_name="PayloadB",
        password="DifferentStrongPassword!42",
        password_confirm="DifferentStrongPassword!42",
    )
    with (
        patch("accounts.services.generate_otp_code", return_value="222222"),
        patch("accounts.services.send_sms_otp"),
    ):
        assert (
            client.post(
                reverse("accounts:register"),
                payload_b,
                content_type="application/json",
            ).status_code
            == 202
        )

    assert verify_registration_otp(PHONE_NUMBER, "111111").status is (
        VerificationStatus.INVALID
    )
    assert verify_registration_otp(PHONE_NUMBER, "222222").status is (
        VerificationStatus.VERIFIED
    )
    user = User.objects.get(phone_number=PHONE_NUMBER)
    assert user.first_name == "PayloadB"
    assert user.check_password("DifferentStrongPassword!42")


@pytest.mark.parametrize(
    "newer_delivery_status",
    (
        None,
        PhoneOTP.DeliveryStatus.FAILED,
        PhoneOTP.DeliveryStatus.UNCERTAIN,
    ),
)
@override_settings(OTP_RESEND_COOLDOWN_SECONDS=1)
def test_pending_or_failed_newer_delivery_does_not_displace_older_success(
    newer_delivery_status,
):
    payload_a = registration_payload()
    payload_a.update(first_name="OlderEligiblePayload")
    older_id, older_code = _prepare_registration_otp(
        PHONE_NUMBER,
        payload_a,
    )
    PhoneOTP.objects.filter(pk=older_id).update(
        created_at=timezone.now() - timedelta(minutes=2)
    )

    payload_b = registration_payload()
    payload_b.update(
        first_name="NewerUndeliveredPayload",
        password="DifferentStrongPassword!42",
        password_confirm="DifferentStrongPassword!42",
    )
    newer_id, newer_code = _prepare_registration_otp(
        PHONE_NUMBER,
        payload_b,
    )

    if newer_delivery_status is not None:
        assert (
            _complete_otp_delivery(
                PHONE_NUMBER,
                newer_id,
                newer_delivery_status,
            )
            is False
        )

    assert (
        _complete_otp_delivery(
            PHONE_NUMBER,
            older_id,
            PhoneOTP.DeliveryStatus.SENT,
        )
        is True
    )

    # A delayed completion for the newer invalidated candidate cannot restore it.
    assert (
        _complete_otp_delivery(
            PHONE_NUMBER,
            newer_id,
            PhoneOTP.DeliveryStatus.SENT,
        )
        is False
    )

    older = PhoneOTP.objects.get(pk=older_id)
    newer = PhoneOTP.objects.get(pk=newer_id)

    assert older.delivery_status == PhoneOTP.DeliveryStatus.SENT
    assert older.invalidated_at is None
    assert newer.invalidated_at is not None

    assert verify_registration_otp(PHONE_NUMBER, newer_code).status is (
        VerificationStatus.INVALID
    )
    assert verify_registration_otp(PHONE_NUMBER, older_code).status is (
        VerificationStatus.VERIFIED
    )

    user = User.objects.get(phone_number=PHONE_NUMBER)
    assert user.first_name == "OlderEligiblePayload"
    assert user.check_password(PASSWORD)
    assert not user.check_password("DifferentStrongPassword!42")


@override_settings(OTP_RESEND_COOLDOWN_SECONDS=1)
def test_out_of_order_delivery_completion_cannot_restore_older_candidate():
    payload_a = registration_payload()
    payload_a.update(first_name="OlderPayload")
    older_id, older_code = _prepare_registration_otp(PHONE_NUMBER, payload_a)
    PhoneOTP.objects.filter(pk=older_id).update(
        created_at=timezone.now() - timedelta(minutes=2)
    )

    payload_b = registration_payload()
    payload_b.update(
        first_name="NewerPayload",
        password="DifferentStrongPassword!42",
        password_confirm="DifferentStrongPassword!42",
    )
    newer_id, newer_code = _prepare_registration_otp(PHONE_NUMBER, payload_b)

    assert (
        _complete_otp_delivery(
            PHONE_NUMBER,
            newer_id,
            PhoneOTP.DeliveryStatus.SENT,
        )
        is True
    )
    assert (
        _complete_otp_delivery(
            PHONE_NUMBER,
            older_id,
            PhoneOTP.DeliveryStatus.SENT,
        )
        is False
    )

    older = PhoneOTP.objects.get(pk=older_id)
    newer = PhoneOTP.objects.get(pk=newer_id)
    assert older.delivery_status == PhoneOTP.DeliveryStatus.SENT
    assert older.invalidated_at is not None
    assert newer.delivery_status == PhoneOTP.DeliveryStatus.SENT
    assert newer.invalidated_at is None
    assert verify_registration_otp(PHONE_NUMBER, older_code).status is (
        VerificationStatus.INVALID
    )
    assert verify_registration_otp(PHONE_NUMBER, newer_code).status is (
        VerificationStatus.VERIFIED
    )
    user = User.objects.get(phone_number=PHONE_NUMBER)
    assert user.first_name == "NewerPayload"
    assert user.check_password("DifferentStrongPassword!42")


def test_delivery_completion_fails_closed_after_user_recreation():
    otp_id, _code = _prepare_registration_otp(
        PHONE_NUMBER,
        registration_payload(),
    )
    pending_user = User.objects.get(phone_number=PHONE_NUMBER)
    pending_user.delete()
    replacement = create_user()

    assert (
        _complete_otp_delivery(
            PHONE_NUMBER,
            otp_id,
            PhoneOTP.DeliveryStatus.SENT,
        )
        is False
    )
    replacement.refresh_from_db()
    assert replacement.is_active is False
    assert replacement.is_phone_verified is False
    assert not PhoneOTP.objects.filter(pk=otp_id).exists()


def test_active_unverified_user_can_recover_only_after_bound_otp(client):
    user = User.objects.create_user(
        phone_number=PHONE_NUMBER,
        password="OldPassword!42",
        first_name="Old",
        last_name="Profile",
        is_active=True,
        is_phone_verified=False,
    )
    payload = registration_payload()
    payload.update(first_name="Recovered", last_name="Account")
    with (
        patch("accounts.services.generate_otp_code", return_value="333333"),
        patch("accounts.services.send_sms_otp"),
    ):
        response = client.post(
            reverse("accounts:register"),
            payload,
            content_type="application/json",
        )
    assert response.status_code == 202
    user.refresh_from_db()
    assert user.first_name == "Old"
    assert user.check_password("OldPassword!42")

    assert verify_registration_otp(PHONE_NUMBER, "333333").status is (
        VerificationStatus.VERIFIED
    )
    user.refresh_from_db()
    assert user.first_name == "Recovered"
    assert user.last_name == "Account"
    assert user.check_password(PASSWORD)


def test_old_otp_cannot_survive_user_deletion_and_recreation():
    user = create_user()
    otp = create_sent_otp(user=user)
    user.delete()
    replacement = create_user()

    assert not PhoneOTP.objects.filter(pk=otp.pk).exists()
    assert verify_registration_otp(replacement.phone_number, OTP_CODE).status is (
        VerificationStatus.INVALID
    )
