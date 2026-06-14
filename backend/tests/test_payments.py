import pytest
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from orders.models import Order, OrderItem
from payments.models import Payment
from products.models import Brand, Category, Product

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def enable_mock_gateway(settings):
    settings.DEBUG = True


@pytest.fixture
def user():
    return User.objects.create_user(
        phone_number="09123456789",
        password="StrongPassword!42",
        first_name="Payment",
        last_name="User",
        is_active=True,
        is_phone_verified=True,
    )


@pytest.fixture
def other_user():
    return User.objects.create_user(
        phone_number="09987654321",
        password="StrongPassword!42",
        first_name="Other",
        last_name="User",
        is_active=True,
        is_phone_verified=True,
    )


@pytest.fixture
def product():
    category = Category.objects.create(name="Payment Toys", slug="payment-toys")
    brand = Brand.objects.create(name="Pay Brand", slug="pay-brand")
    return Product.objects.create(
        category=category,
        brand=brand,
        name="Payment Toy",
        slug="payment-toy",
        description="A toy used for payment tests.",
        sku="PAY-001",
        price=1000,
        stock=10,
        age_group=Product.AgeGroup.THREE_TO_FIVE,
        gender=Product.Gender.UNISEX,
    )


@pytest.fixture
def order(user, product):
    order = Order.objects.create(
        user=user,
        total_amount=2000,
        shipping_address="123 Payment Street",
        postal_code="1234567890",
        recipient_name="Payment User",
        recipient_phone=user.phone_number,
    )
    OrderItem.objects.create(
        order=order,
        product=product,
        product_name=product.name,
        product_price=1000,
        quantity=2,
        line_total=2000,
    )
    return order


def auth(user):
    token = RefreshToken.for_user(user).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def request_payment(client, user, order):
    return client.post(
        reverse("payments:request"),
        {"order_id": order.id},
        content_type="application/json",
        **auth(user),
    )


def verify_payment(client, payment, status="OK"):
    return client.post(
        reverse("payments:verify"),
        {"authority": payment.authority, "status": status},
        content_type="application/json",
    )


def test_request_payment_for_own_pending_order(client, user, order):
    response = request_payment(client, user, order)

    assert response.status_code == 201
    payment = Payment.objects.get(order=order)
    assert payment.user == user
    assert payment.status == Payment.Status.PENDING
    assert payment.amount == order.total_amount
    assert payment.authority.startswith("mock-")
    assert response.json()["payment_url"].endswith(f"?authority={payment.authority}")


def test_cannot_pay_another_users_order(client, other_user, order):
    response = request_payment(client, other_user, order)

    assert response.status_code == 400
    assert Payment.objects.count() == 0


def test_cannot_pay_already_paid_order(client, user, order):
    order.status = Order.Status.PAID
    order.stock_reduced = True
    order.save(update_fields=("status", "stock_reduced"))

    response = request_payment(client, user, order)

    assert response.status_code == 400
    assert Payment.objects.count() == 0


def test_existing_pending_payment_is_reused(client, user, order):
    first_response = request_payment(client, user, order)
    first_payment_id = first_response.json()["id"]

    second_response = request_payment(client, user, order)

    assert second_response.status_code == 201
    assert second_response.json()["id"] == first_payment_id
    assert Payment.objects.count() == 1


def test_verify_success_marks_payment_and_order_paid_and_reduces_stock(
    client,
    user,
    order,
    product,
):
    request_payment(client, user, order)
    payment = Payment.objects.get(order=order)

    response = verify_payment(client, payment)

    assert response.status_code == 200
    payment.refresh_from_db()
    order.refresh_from_db()
    product.refresh_from_db()
    assert payment.status == Payment.Status.PAID
    assert payment.ref_id.startswith("MOCK-")
    assert payment.paid_at is not None
    assert order.status == Order.Status.PAID
    assert order.stock_reduced is True
    assert product.stock == 8


def test_verify_success_does_not_reduce_stock_twice(client, user, order, product):
    request_payment(client, user, order)
    payment = Payment.objects.get(order=order)

    first_response = verify_payment(client, payment)
    second_response = verify_payment(client, payment)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    product.refresh_from_db()
    assert product.stock == 8


def test_verify_failure_marks_payment_failed(client, user, order, product):
    request_payment(client, user, order)
    payment = Payment.objects.get(order=order)

    response = verify_payment(client, payment, status="NOK")

    assert response.status_code == 200
    payment.refresh_from_db()
    order.refresh_from_db()
    product.refresh_from_db()
    assert payment.status == Payment.Status.FAILED
    assert order.status == Order.Status.PENDING
    assert order.stock_reduced is False
    assert product.stock == 10


def test_insufficient_stock_during_verify_fails_gracefully(
    client,
    user,
    order,
    product,
):
    request_payment(client, user, order)
    payment = Payment.objects.get(order=order)
    product.stock = 1
    product.save(update_fields=("stock",))

    response = verify_payment(client, payment)

    assert response.status_code == 400
    payment.refresh_from_db()
    order.refresh_from_db()
    product.refresh_from_db()
    assert "Insufficient stock" in str(response.json())
    assert payment.status == Payment.Status.PENDING
    assert order.status == Order.Status.PENDING
    assert order.stock_reduced is False
    assert product.stock == 1
