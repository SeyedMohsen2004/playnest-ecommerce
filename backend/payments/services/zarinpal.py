from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests
from django.conf import settings


def mask_card_pan(value: Any) -> str | None:
    if value in (None, ""):
        return None
    digits = "".join(character for character in str(value) if character.isdigit())
    if len(digits) >= 10:
        return f"{digits[:6]}******{digits[-4:]}"
    return "****"


class ZarinPalError(Exception):
    """Base exception for safe, non-secret ZarinPal errors."""

    def __init__(
        self,
        message: str,
        *,
        code: int | None = None,
        gateway_response: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.gateway_response = gateway_response or {}


class ZarinPalTransportError(ZarinPalError):
    """The outcome is unknown because the gateway was unreachable."""


class ZarinPalVerificationError(ZarinPalError):
    """ZarinPal definitively rejected a verification request."""


@dataclass(frozen=True)
class ZarinPalEndpoints:
    request_url: str
    verify_url: str
    start_pay_url: str


@dataclass(frozen=True)
class PaymentCreationResult:
    authority: str
    payment_url: str
    code: int
    message: str
    gateway_response: dict[str, Any]


@dataclass(frozen=True)
class PaymentVerificationResult:
    code: int
    message: str
    ref_id: str | None
    card_pan: str | None
    card_hash: str
    fee: int | None
    fee_type: str
    gateway_response: dict[str, Any]

    @property
    def is_successful(self) -> bool:
        return self.code in (100, 101)


class ZarinPalService:
    PRODUCTION_ENDPOINTS = ZarinPalEndpoints(
        request_url="https://payment.zarinpal.com/pg/v4/payment/request.json",
        verify_url="https://payment.zarinpal.com/pg/v4/payment/verify.json",
        start_pay_url="https://payment.zarinpal.com/pg/StartPay",
    )
    SANDBOX_ENDPOINTS = ZarinPalEndpoints(
        request_url="https://sandbox.zarinpal.com/pg/v4/payment/request.json",
        verify_url="https://sandbox.zarinpal.com/pg/v4/payment/verify.json",
        start_pay_url="https://sandbox.zarinpal.com/pg/StartPay",
    )
    TIMEOUT_SECONDS = 15
    JSON_HEADERS = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    SAFE_DATA_FIELDS = {
        "code",
        "message",
        "authority",
        "ref_id",
        "card_pan",
        "card_hash",
        "fee",
        "fee_type",
    }

    def __init__(
        self,
        merchant_id: str | None = None,
        sandbox: bool | None = None,
        callback_url: str | None = None,
    ) -> None:
        self.merchant_id = (merchant_id or settings.ZARINPAL_MERCHANT_ID).strip()
        self.sandbox = settings.ZARINPAL_SANDBOX if sandbox is None else sandbox
        self.callback_url = callback_url or settings.ZARINPAL_CALLBACK_URL
        self.endpoints = (
            self.SANDBOX_ENDPOINTS if self.sandbox else self.PRODUCTION_ENDPOINTS
        )

    def create_payment(self, order) -> PaymentCreationResult:
        self._validate_merchant_id()
        payload = {
            "merchant_id": self.merchant_id,
            "amount": int(order.total_amount),
            "currency": "IRT",
            "description": f"Order #{order.id}",
            "callback_url": self.callback_url,
            "metadata": {
                "mobile": order.recipient_phone or order.user.phone_number,
                "email": getattr(order.user, "email", "") or "",
                "order_id": str(order.id),
            },
        }
        response_data = self._post(self.endpoints.request_url, payload)
        data = self._extract_success_data(response_data, expected_codes=(100,))
        authority = str(data.get("authority") or "").strip()
        if not authority:
            raise ZarinPalError(
                "ZarinPal did not return a payment authority.",
                code=self._normalize_int(data.get("code")),
                gateway_response=response_data,
            )
        return PaymentCreationResult(
            authority=authority,
            payment_url=self.payment_url(authority),
            code=self._normalize_int(data.get("code")) or 100,
            message=str(data.get("message") or ""),
            gateway_response=response_data,
        )

    def verify_payment(
        self,
        authority: str,
        amount: int,
    ) -> PaymentVerificationResult:
        self._validate_merchant_id()
        payload = {
            "merchant_id": self.merchant_id,
            "amount": int(amount),
            "authority": authority,
        }
        response_data = self._post(self.endpoints.verify_url, payload)
        try:
            data = self._extract_success_data(
                response_data,
                expected_codes=(100, 101),
            )
        except ZarinPalError as exc:
            raise ZarinPalVerificationError(
                str(exc),
                code=exc.code,
                gateway_response=exc.gateway_response,
            ) from exc

        code = self._normalize_int(data.get("code"))
        if code not in (100, 101):
            raise ZarinPalVerificationError(
                "ZarinPal verification was not successful.",
                code=code,
                gateway_response=response_data,
            )
        return PaymentVerificationResult(
            code=code,
            message=str(data.get("message") or ""),
            ref_id=self._normalize_optional_string(data.get("ref_id")),
            card_pan=mask_card_pan(data.get("card_pan")),
            card_hash=str(data.get("card_hash") or ""),
            fee=self._normalize_int(data.get("fee")),
            fee_type=str(data.get("fee_type") or ""),
            gateway_response=response_data,
        )

    def payment_url(self, authority: str) -> str:
        return f"{self.endpoints.start_pay_url}/{authority}"

    def _validate_merchant_id(self) -> None:
        if not self.merchant_id:
            raise ZarinPalError("ZarinPal merchant id is not configured.")

    def _post(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = requests.post(
                url,
                json=payload,
                headers=self.JSON_HEADERS,
                timeout=self.TIMEOUT_SECONDS,
            )
        except requests.Timeout as exc:
            raise ZarinPalTransportError("ZarinPal request timed out.") from exc
        except requests.ConnectionError as exc:
            raise ZarinPalTransportError("Could not connect to ZarinPal.") from exc
        except requests.RequestException as exc:
            raise ZarinPalTransportError("ZarinPal request failed.") from exc

        try:
            raw_data = response.json()
        except ValueError as exc:
            raise ZarinPalTransportError(
                "ZarinPal returned an invalid response."
            ) from exc
        if not isinstance(raw_data, dict):
            raise ZarinPalTransportError("ZarinPal returned an unexpected response.")

        data = self._sanitize_response(raw_data)
        if not 200 <= response.status_code < 300:
            raise ZarinPalTransportError(
                self._extract_error_message(data),
                code=self._response_code(data),
                gateway_response=data,
            )
        return data

    def _extract_success_data(
        self,
        response_data: dict[str, Any],
        expected_codes: tuple[int, ...],
    ) -> dict[str, Any]:
        data = response_data.get("data") or {}
        code = self._normalize_int(data.get("code")) if isinstance(data, dict) else None
        if isinstance(data, dict) and code in expected_codes:
            return data

        message = self._extract_error_message(response_data)
        raise ZarinPalError(
            message,
            code=code or self._response_code(response_data),
            gateway_response=response_data,
        )

    def _sanitize_response(self, response_data: dict[str, Any]) -> dict[str, Any]:
        sanitized: dict[str, Any] = {}
        data = response_data.get("data")
        if isinstance(data, dict):
            sanitized["data"] = {
                key: value
                for key, value in data.items()
                if key in self.SAFE_DATA_FIELDS
            }
            if "card_pan" in sanitized["data"]:
                sanitized["data"]["card_pan"] = mask_card_pan(
                    sanitized["data"]["card_pan"]
                )
        errors = response_data.get("errors")
        if isinstance(errors, dict):
            sanitized["errors"] = {
                key: errors[key] for key in ("code", "message") if key in errors
            }
        elif isinstance(errors, list):
            sanitized["errors"] = [str(item)[:255] for item in errors[:3]]
        return sanitized

    def _extract_error_message(self, response_data: dict[str, Any]) -> str:
        errors = response_data.get("errors") or {}
        if isinstance(errors, dict):
            message = errors.get("message") or errors.get("code")
            if message:
                return f"ZarinPal error: {message}"
        if isinstance(errors, list) and errors:
            return f"ZarinPal error: {errors[0]}"
        data = response_data.get("data") or {}
        if isinstance(data, dict) and data.get("message"):
            return f"ZarinPal error: {data['message']}"
        return "ZarinPal payment request was not successful."

    def _response_code(self, response_data: dict[str, Any]) -> int | None:
        errors = response_data.get("errors") or {}
        if isinstance(errors, dict):
            return self._normalize_int(errors.get("code"))
        data = response_data.get("data") or {}
        if isinstance(data, dict):
            return self._normalize_int(data.get("code"))
        return None

    @staticmethod
    def _normalize_int(value: Any) -> int | None:
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _normalize_optional_string(value: Any) -> str | None:
        if value in (None, ""):
            return None
        return str(value)
