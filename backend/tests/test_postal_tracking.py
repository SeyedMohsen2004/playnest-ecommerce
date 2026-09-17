from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

import pytest
from django.contrib import admin
from django.contrib.admin.models import CHANGE, LogEntry
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connections
from django.db.migrations.executor import MigrationExecutor
from django.test import RequestFactory
from django.urls import reverse
from drf_spectacular.generators import SchemaGenerator
from rest_framework.test import APIClient

from accounts.models import User
from orders.models import Order
from orders.services import transition_fulfillment_orders, update_order_postal_tracking

pytestmark = pytest.mark.django_db


@pytest.fixture
def owner():
    return User.objects.create_user(
        phone_number="09120000001",
        password="SyntheticPassword!42",
        is_active=True,
        is_phone_verified=True,
    )


@pytest.fixture
def staff():
    return User.objects.create_superuser("09120000002", "SyntheticPassword!42")


def make_order(owner, status=Order.Status.PROCESSING, code=""):
    return Order.objects.create(
        user=owner,
        status=status,
        postal_tracking_code=code,
        shipping_address="Synthetic address",
        postal_code="1234567890",
        recipient_name="Synthetic recipient",
        recipient_phone=owner.phone_number,
    )


def test_tracking_normalization_and_historical_orders(owner):
    order = make_order(owner, Order.Status.DELIVERED)
    assert order.postal_tracking_code == ""
    order = make_order(owner, code="  POST-۱۲۳-abc  ")
    order.refresh_from_db()
    assert order.postal_tracking_code == "POST-۱۲۳-abc"
    for invalid in ("   ", "x" * 101):
        with pytest.raises(ValidationError):
            update_order_postal_tracking(order.pk, invalid)
    assert Order.objects.get(pk=order.pk).postal_tracking_code == "POST-۱۲۳-abc"


def test_shipping_requires_tracking_for_entire_eligible_selection(owner):
    valid = make_order(owner, code="POST-123")
    missing = make_order(owner)
    with pytest.raises(ValidationError):
        transition_fulfillment_orders([valid.pk, missing.pk], to_status="shipped")
    assert set(Order.objects.values_list("status", flat=True)) == {"processing"}
    update_order_postal_tracking(missing.pk, "POST-456")
    assert (
        len(transition_fulfillment_orders([valid.pk, missing.pk], to_status="shipped"))
        == 2
    )
    transition_fulfillment_orders([valid.pk], to_status="delivered")
    valid.refresh_from_db()
    assert valid.status == "delivered"
    assert valid.postal_tracking_code == "POST-123"


@pytest.mark.parametrize("status", Order.Status.values)
def test_tracking_edit_state_and_admin_form_restrictions(owner, staff, status):
    order = make_order(owner, status, "ORIGINAL")
    editable = status in ("processing", "shipped")
    request = RequestFactory().get("/")
    request.user = staff
    model_admin = admin.site._registry[Order]
    form = model_admin.get_form(request, order)
    assert ("postal_tracking_code" in form.base_fields) == editable
    if editable:
        update_order_postal_tracking(order.pk, " CORRECTED ")
        assert Order.objects.get(pk=order.pk).postal_tracking_code == "CORRECTED"
    else:
        with pytest.raises(ValidationError):
            update_order_postal_tracking(order.pk, "FORGED")
        assert Order.objects.get(pk=order.pk).postal_tracking_code == "ORIGINAL"


def admin_post(client, order, code):
    return client.post(
        reverse("admin:orders_order_change", args=[order.pk]),
        {
            "recipient_name": order.recipient_name,
            "recipient_phone": order.recipient_phone,
            "shipping_address": order.shipping_address,
            "postal_code": order.postal_code,
            "postal_tracking_code": code,
            "items-TOTAL_FORMS": "0",
            "items-INITIAL_FORMS": "0",
            "payments-TOTAL_FORMS": "0",
            "payments-INITIAL_FORMS": "0",
            "_save": "Save",
        },
    )


@pytest.mark.parametrize("status", Order.Status.values)
def test_real_admin_post_and_history(client, owner, staff, status):
    order = make_order(owner, status, "ORIGINAL")
    client.force_login(staff)
    response = admin_post(client, order, " CORRECTED ")
    assert response.status_code == 302
    order.refresh_from_db()
    if status in ("processing", "shipped"):
        assert order.postal_tracking_code == "CORRECTED"
        entry = LogEntry.objects.get(
            object_id=str(order.pk),
            action_flag=CHANGE,
        )
        assert "کد رهگیری پستی" in entry.get_change_message()
    else:
        assert order.postal_tracking_code == "ORIGINAL"


def test_admin_rejects_blank_tracking_and_unauthorized_edit(client, owner, staff):
    order = make_order(owner, "shipped", "ORIGINAL")
    client.force_login(staff)
    for code in ("", "   ", "x" * 101):
        assert admin_post(client, order, code).status_code == 200
        assert Order.objects.get(pk=order.pk).postal_tracking_code == "ORIGINAL"
    client.force_login(owner)
    assert admin_post(client, order, "FORGED").status_code == 302
    assert Order.objects.get(pk=order.pk).postal_tracking_code == "ORIGINAL"


def test_admin_bulk_shipping_refuses_missing_code_without_partial_change(owner, staff):
    make_order(owner, code="VALID")
    make_order(owner)
    request = RequestFactory().post("/")
    request.user = staff
    model_admin = admin.site._registry[Order]
    with patch.object(model_admin, "message_user") as message:
        model_admin.mark_as_shipped(request, Order.objects.all())
    assert "هیچ سفارشی تغییر نکرد" in message.call_args.args[1]
    assert not LogEntry.objects.exists()
    assert set(Order.objects.values_list("status", flat=True)) == {"processing"}


@pytest.mark.parametrize("status", Order.Status.values)
def test_customer_visibility_list_detail_and_ownership(owner, status):
    order = make_order(owner, status, "PRIVATE-TRACKING")
    client = APIClient()
    client.force_authenticate(owner)
    expected = "PRIVATE-TRACKING" if status in ("shipped", "delivered") else None
    detail_url = reverse("orders:order-detail", args=[order.pk])
    assert client.get(detail_url).data["postal_tracking_code"] == expected
    listing = client.get(reverse("orders:order-list")).data
    assert listing[0]["postal_tracking_code"] == expected
    other = User.objects.create_user(
        "09120000003", "SyntheticPassword!42", is_phone_verified=True
    )
    client.force_authenticate(other)
    assert client.get(detail_url).status_code == 404
    assert client.get(reverse("orders:order-list")).data == []
    client.force_authenticate(None)
    assert client.get(detail_url).status_code == 401


def test_customer_cannot_write_tracking_and_schema_is_read_only(owner):
    order = make_order(owner, "paid")
    client = APIClient()
    client.force_authenticate(owner)
    assert (
        client.patch(
            reverse("orders:order-detail", args=[order.pk]),
            {"postal_tracking_code": "FORGED"},
            format="json",
        ).status_code
        == 405
    )
    assert (
        client.patch(
            reverse("orders:order-shipping", args=[order.pk]),
            {"postal_tracking_code": "FORGED"},
            format="json",
        ).status_code
        == 200
    )
    order.refresh_from_db()
    assert order.postal_tracking_code == ""
    schemas = SchemaGenerator().get_schema(public=True)["components"]["schemas"]
    field = schemas["Order"]["properties"]["postal_tracking_code"]
    assert field["readOnly"] and field["nullable"]
    assert "postal_tracking_code" not in schemas["Checkout"]["properties"]


@pytest.mark.django_db(transaction=True)
def test_concurrent_delivery_and_tracking_edit_preserve_state(owner):
    order = make_order(owner, "shipped", "ORIGINAL")
    barrier = Barrier(2)

    def worker(deliver):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            if deliver:
                transition_fulfillment_orders([order.pk], to_status="delivered")
                return "delivered"
            try:
                update_order_postal_tracking(order.pk, "CORRECTED")
                return "edited"
            except ValidationError:
                return "rejected"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(worker, (True, False)))
    order.refresh_from_db()
    assert order.status == "delivered"
    assert order.postal_tracking_code == (
        "CORRECTED" if results[1] == "edited" else "ORIGINAL"
    )
    with pytest.raises(ValidationError):
        update_order_postal_tracking(order.pk, "TOO-LATE")


@pytest.mark.django_db(transaction=True)
def test_upgrade_preserves_historical_order():
    connection = connections["default"]
    old = [("orders", "0013_coupon_per_user_usage_limit")]
    latest = [("orders", "0014_order_postal_tracking_code")]
    executor = MigrationExecutor(connection)
    executor.migrate(old)
    try:
        apps = executor.loader.project_state(old).apps
        user = apps.get_model("accounts", "User").objects.create(
            phone_number="09120000004"
        )
        order = apps.get_model("orders", "Order").objects.create(
            user_id=user.pk,
            status="delivered",
            shipping_address="Synthetic",
            postal_code="1234567890",
            recipient_name="Synthetic",
            recipient_phone=user.phone_number,
        )
        executor = MigrationExecutor(connection)
        executor.migrate(latest)
        restored = Order.objects.get(pk=order.pk)
        assert restored.status == "delivered"
        assert restored.user_id == user.pk
        assert restored.postal_tracking_code == ""
    finally:
        MigrationExecutor(connection).migrate(latest)
