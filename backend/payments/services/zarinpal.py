from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests
from django.conf import settings


class ZarinPalError(Exception):
    """Raised when ZarinPal rejects a request or cannot be reached."""


@dataclass(frozen=True)
class ZarinPalEndpoints:
    request_url: str
    verify_url: str
    start_pay_url: str


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

    def create_payment(self, order) -> dict[str, Any]:
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
        authority = data.get("authority")
        if not authority:
            raise ZarinPalError("ZarinPal did not return a payment authority.")
        return {
            "authority": authority,
            "payment_url": self.payment_url(authority),
            "gateway_response": response_data,
        }

    def verify_payment(self, authority: str, amount: int) -> dict[str, Any]:
        self._validate_merchant_id()
        payload = {
            "merchant_id": self.merchant_id,
            "amount": int(amount),
            "authority": authority,
        }
        response_data = self._post(self.endpoints.verify_url, payload)
        data = self._extract_success_data(response_data, expected_codes=(100, 101))
        return {
            "ref_id": data.get("ref_id"),
            "card_pan": data.get("card_pan"),
            "gateway_response": response_data,
        }

    def payment_url(self, authority: str) -> str:
        return f"{self.endpoints.start_pay_url}/{authority}"

    def _validate_merchant_id(self) -> None:
        if not self.merchant_id:
            raise ZarinPalError("ZarinPal merchant id is not configured.")

    def _post(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = requests.post(url, json=payload, timeout=self.TIMEOUT_SECONDS)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise ZarinPalError("Could not connect to ZarinPal.") from exc
        except ValueError as exc:
            raise ZarinPalError("ZarinPal returned an invalid response.") from exc
        if not isinstance(data, dict):
            raise ZarinPalError("ZarinPal returned an unexpected response.")
        return data

    def _extract_success_data(
        self,
        response_data: dict[str, Any],
        expected_codes: tuple[int, ...],
    ) -> dict[str, Any]:
        data = response_data.get("data") or {}
        if isinstance(data, dict) and data.get("code") in expected_codes:
            return data

        message = self._extract_error_message(response_data)
        raise ZarinPalError(message)

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
