from unittest.mock import patch

import pytest
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from orders.models import Cart, CartItem, Order, ShippingSettings
from payments.models import Payment
from payments.services.zarinpal import PaymentCreationResult
from products.models import Brand, Category, Product

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(
        phone_number="09123334444",
        password="StrongPassword!42",
        first_name="Shipping",
        last_name="Customer",
        is_active=True,
        is_phone_verified=True,
    )


@pytest.fixture
def admin_user():
    return User.objects.create_superuser(
        phone_number="09001112222",
        password="StrongPassword!42",
    )


@pytest.fixture
def product():
    category = Category.objects.create(name="Shipping Toys", slug="shipping-toys")
    brand = Brand.objects.create(name="Shipping Brand", slug="shipping-brand")
    return Product.objects.create(
        category=category,
        brand=brand,
        name="Shipping Test Toy",
        slug="shipping-test-toy",
        description="Shipping test product.",
        sku="SHIP-001",
        price=1_000_000,
        stock=20,
        age_group=Product.AgeGroup.THREE_TO_FIVE,
        gender=Product.Gender.UNISEX,
    )


def auth(user):
    token = RefreshToken.for_user(user).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def add_to_cart(user, product, quantity=1):
    cart, _created = Cart.objects.get_or_create(user=user)
    return CartItem.objects.create(cart=cart, product=product, quantity=quantity)


def checkout_payload(shipping_zone=None, **extra):
    payload = {
        "shipping_address": "Tabriz shipping address",
        "postal_code": "1234567890",
        "recipient_name": "Shipping Customer",
        "recipient_phone": "09123334444",
    }
    if shipping_zone is not None:
        payload["shipping_zone"] = shipping_zone
    payload.update(extra)
    return payload


def checkout(client, user, shipping_zone, **extra):
    return client.post(
        reverse("orders:checkout"),
        checkout_payload(shipping_zone, **extra),
        content_type="application/json",
        **auth(user),
    )


def configure_rates(*, tabriz=100_000, nationwide=150_000):
    shipping_settings = ShippingSettings.load()
    shipping_settings.tabriz_shipping_fee = tabriz
    shipping_settings.nationwide_shipping_fee = nationwide
    shipping_settings.save()
    return shipping_settings


def payment_creation_result():
    return PaymentCreationResult(
        authority="S" * 36,
        payment_url=f"https://sandbox.zarinpal.com/pg/StartPay/{'S' * 36}",
        code=100,
        message="Success",
        gateway_response={"data": {"code": 100, "authority": "S" * 36}},
    )


def test_shipping_settings_loads_one_effective_singleton():
    first = ShippingSettings.load()
    second = ShippingSettings.load()

    assert first.pk == ShippingSettings.SINGLETON_PK
    assert second.pk == first.pk
    assert ShippingSettings.objects.count() == 1
    assert first.tabriz_shipping_fee == 50_000
    assert first.nationwide_shipping_fee == 50_000


def test_shipping_settings_admin_edits_both_rates(client, admin_user):
    shipping_settings = ShippingSettings.load()
    client.force_login(admin_user)

    response = client.post(
        reverse(
            "admin:orders_shippingsettings_change",
            args=(shipping_settings.pk,),
        ),
        {
            "tabriz_shipping_fee": 110_000,
            "nationwide_shipping_fee": 175_000,
            "_save": "Save",
        },
    )

    assert response.status_code == 302
    shipping_settings.refresh_from_db()
    assert shipping_settings.tabriz_shipping_fee == 110_000
    assert shipping_settings.nationwide_shipping_fee == 175_000


def test_shipping_settings_rejects_negative_rates(client, admin_user):
    shipping_settings = ShippingSettings.load()
    shipping_settings.tabriz_shipping_fee = -1
    with pytest.raises(ValidationError):
        shipping_settings.full_clean()

    client.force_login(admin_user)
    response = client.post(
        reverse(
            "admin:orders_shippingsettings_change",
            args=(shipping_settings.pk,),
        ),
        {
            "tabriz_shipping_fee": -1,
            "nationwide_shipping_fee": 150_000,
            "_save": "Save",
        },
    )

    assert response.status_code == 200
    shipping_settings.refresh_from_db()
    assert shipping_settings.tabriz_shipping_fee == 50_000


def test_shipping_settings_admin_is_singleton_and_not_deletable(admin_user):
    ShippingSettings.load()
    settings_admin = admin.site._registry[ShippingSettings]

    assert settings_admin.has_add_permission(type("Request", (), {"user": admin_user})()) is False
    assert settings_admin.has_delete_permission(None) is False


def test_public_shipping_rates_api_returns_both_current_values(client):
    configure_rates(tabriz=100_000, nationwide=150_000)

    response = client.get(reverse("orders:shipping-rates"))

    assert response.status_code == 200
    assert response.json() == {
        "tabriz": {"label": "داخل تبریز", "fee": 100_000},
        "nationwide": {"label": "سایر نقاط کشور", "fee": 150_000},
    }


def test_checkout_requires_shipping_zone(client, user, product):
    add_to_cart(user, product)

    response = client.post(
        reverse("orders:checkout"),
        checkout_payload(),
        content_type="application/json",
        **auth(user),
    )

    assert response.status_code == 400
    assert "shipping_zone" in response.json()
    assert Order.objects.count() == 0


def test_checkout_rejects_invalid_shipping_zone(client, user, product):
    add_to_cart(user, product)

    response = checkout(client, user, "unknown-zone")

    assert response.status_code == 400
    assert "shipping_zone" in response.json()
    assert Order.objects.count() == 0


@pytest.mark.parametrize(
    ("shipping_zone", "expected_fee"),
    ((Order.ShippingZone.TABRIZ, 100_000), (Order.ShippingZone.NATIONWIDE, 150_000)),
)
def test_checkout_uses_selected_server_rate(
    client,
    user,
    product,
    shipping_zone,
    expected_fee,
):
    configure_rates()
    add_to_cart(user, product)

    response = checkout(client, user, shipping_zone)

    assert response.status_code == 201
    order = Order.objects.get(user=user)
    assert order.shipping_zone == shipping_zone
    assert order.shipping_cost == expected_fee
    assert order.subtotal_amount == 1_000_000
    assert order.total_amount == 1_000_000 + expected_fee


def test_checkout_rejects_client_supplied_shipping_amount(client, user, product):
    configure_rates(tabriz=100_000)
    add_to_cart(user, product)

    response = checkout(
        client,
        user,
        Order.ShippingZone.TABRIZ,
        shipping_cost=1,
    )

    assert response.status_code == 400
    assert "shipping_cost" in response.json()
    assert Order.objects.count() == 0


def test_rate_change_does_not_mutate_existing_order_snapshot(client, user, product):
    configure_rates(tabriz=100_000)
    add_to_cart(user, product)
    response = checkout(client, user, Order.ShippingZone.TABRIZ)
    assert response.status_code == 201
    order = Order.objects.get(user=user)

    configure_rates(tabriz=140_000)
    order.refresh_from_db()

    assert order.shipping_cost == 100_000
    assert order.total_amount == 1_100_000


def test_zarinpal_request_uses_order_total_including_shipping(client, user, product):
    configure_rates(nationwide=150_000)
    add_to_cart(user, product)
    checkout(client, user, Order.ShippingZone.NATIONWIDE)
    order = Order.objects.get(user=user)

    with patch(
        "payments.services.ZarinPalService.create_payment",
        return_value=payment_creation_result(),
    ) as create_payment:
        response = client.post(
            reverse("payments:request"),
            {"order_id": order.id},
            content_type="application/json",
            **auth(user),
        )

    assert response.status_code == 201
    requested_order = create_payment.call_args.args[0]
    assert requested_order.total_amount == 1_150_000
    payment = Payment.objects.get(order=order)
    assert payment.amount == order.total_amount == 1_150_000


def test_retry_payment_uses_original_shipping_snapshot(client, user, product):
    configure_rates(tabriz=100_000)
    add_to_cart(user, product)
    checkout(client, user, Order.ShippingZone.TABRIZ)
    order = Order.objects.get(user=user)
    order.status = Order.Status.PAYMENT_FAILED
    order.save(update_fields=("status",))
    configure_rates(tabriz=190_000)

    with patch(
        "payments.services.ZarinPalService.create_payment",
        return_value=payment_creation_result(),
    ) as create_payment:
        response = client.post(
            reverse("payments:request"),
            {"order_id": order.id},
            content_type="application/json",
            **auth(user),
        )

    assert response.status_code == 201
    requested_order = create_payment.call_args.args[0]
    assert requested_order.shipping_cost == 100_000
    assert requested_order.total_amount == 1_100_000
    assert Payment.objects.get(order=order).amount == 1_100_000


def test_failed_callback_preserves_shipping_snapshot(client, settings, user, product):
    settings.FRONTEND_BASE_URL = "https://ipaktoys.ir"
    configure_rates(nationwide=150_000)
    add_to_cart(user, product)
    checkout(client, user, Order.ShippingZone.NATIONWIDE)
    order = Order.objects.get(user=user)
    payment = Payment.objects.create(
        user=user,
        order=order,
        amount=order.total_amount,
        authority="N" * 36,
    )

    response = client.get(
        reverse("payments:zarinpal-callback"),
        {"Authority": payment.authority, "Status": "NOK"},
    )

    assert response.status_code == 302
    order.refresh_from_db()
    assert order.status == Order.Status.PAYMENT_FAILED
    assert order.shipping_zone == Order.ShippingZone.NATIONWIDE
    assert order.shipping_cost == 150_000
    assert order.total_amount == 1_150_000


def test_order_detail_exposes_snapshot_and_legacy_orders_remain_serializable(
    client,
    user,
    product,
):
    configure_rates(tabriz=100_000)
    add_to_cart(user, product)
    checkout(client, user, Order.ShippingZone.TABRIZ)
    order = Order.objects.get(user=user)

    response = client.get(
        reverse("orders:order-detail", args=(order.id,)),
        **auth(user),
    )

    assert response.status_code == 200
    assert response.json()["shipping_zone"] == "tabriz"
    assert response.json()["shipping_zone_display"] == "داخل تبریز"
    assert response.json()["shipping_cost"] == 100_000

    legacy_order = Order.objects.create(
        user=user,
        shipping_cost=75_000,
        total_amount=75_000,
        shipping_address="Legacy address",
        postal_code="1234567890",
        recipient_name="Legacy recipient",
        recipient_phone=user.phone_number,
    )
    legacy_response = client.get(
        reverse("orders:order-detail", args=(legacy_order.id,)),
        **auth(user),
    )

    assert legacy_response.status_code == 200
    assert legacy_response.json()["shipping_zone"] is None
    assert legacy_response.json()["shipping_zone_display"] == "ثبت نشده"
    assert legacy_response.json()["shipping_cost"] == 75_000
