import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from orders.models import Cart, CartItem, Order, OrderItem
from products.models import Brand, Category, Product

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(
        phone_number="09123456789",
        password="StrongPassword!42",
        first_name="Cart",
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
def admin():
    return User.objects.create_superuser(
        phone_number="09000000000",
        password="StrongPassword!42",
    )


@pytest.fixture
def product():
    category = Category.objects.create(name="Vehicles", slug="vehicles")
    brand = Brand.objects.create(name="PlayNest", slug="playnest-orders")
    return Product.objects.create(
        category=category,
        brand=brand,
        name="Toy Car",
        slug="toy-car",
        description="A fast toy car.",
        sku="CAR-001",
        price=1000,
        discount_price=800,
        stock=10,
        age_group=Product.AgeGroup.THREE_TO_FIVE,
        gender=Product.Gender.UNISEX,
    )


def auth(user):
    token = RefreshToken.for_user(user).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def checkout_payload():
    return {
        "shipping_address": "123 Play Street",
        "postal_code": "1234567890",
        "recipient_name": "Play User",
        "recipient_phone": "09123456789",
    }


def create_order(user, product):
    order = Order.objects.create(
        user=user,
        total_amount=product.final_price,
        shipping_address="123 Play Street",
        postal_code="1234567890",
        recipient_name="Play User",
        recipient_phone=user.phone_number,
    )
    OrderItem.objects.create(
        order=order,
        product=product,
        product_name=product.name,
        product_price=product.final_price,
        quantity=1,
        line_total=product.final_price,
    )
    return order


def test_add_to_cart(client, user, product):
    response = client.post(
        reverse("orders:cart-item-list"),
        {"product": product.id, "quantity": 2},
        content_type="application/json",
        **auth(user),
    )

    assert response.status_code == 201
    item = CartItem.objects.get(cart__user=user, product=product)
    assert item.quantity == 2
    cart_response = client.get(reverse("orders:cart"), **auth(user))
    assert cart_response.json()["total_items"] == 2
    assert cart_response.json()["total_price"] == 1600


def test_update_quantity(client, user, product):
    item = CartItem.objects.create(
        cart=Cart.objects.create(user=user),
        product=product,
        quantity=1,
    )

    response = client.patch(
        reverse("orders:cart-item-detail", args=(item.id,)),
        {"quantity": 4},
        content_type="application/json",
        **auth(user),
    )

    assert response.status_code == 200
    item.refresh_from_db()
    assert item.quantity == 4


def test_remove_from_cart(client, user, product):
    item = CartItem.objects.create(
        cart=Cart.objects.create(user=user),
        product=product,
        quantity=1,
    )

    response = client.delete(
        reverse("orders:cart-item-detail", args=(item.id,)),
        **auth(user),
    )

    assert response.status_code == 204
    assert CartItem.objects.filter(pk=item.pk).exists() is False


def test_checkout_creates_order_without_reducing_stock(client, user, product):
    CartItem.objects.create(
        cart=Cart.objects.create(user=user),
        product=product,
        quantity=3,
    )

    response = client.post(
        reverse("orders:checkout"),
        checkout_payload(),
        content_type="application/json",
        **auth(user),
    )

    assert response.status_code == 201
    order = Order.objects.get(user=user)
    order_item = order.items.get()
    assert order.subtotal_amount == 2400
    assert order.discount_amount == 0
    assert order.shipping_cost == 50000
    assert order.total_amount == 52400
    assert order_item.product_name == product.name
    assert order_item.product_price == 800
    assert order_item.quantity == 3
    assert order_item.line_total == 2400
    assert CartItem.objects.filter(cart__user=user).exists() is False
    assert order.status == Order.Status.PENDING
    assert order.stock_reduced is False
    product.refresh_from_db()
    assert product.stock == 10


def test_mark_as_paid_reduces_stock(client, user, product):
    CartItem.objects.create(
        cart=Cart.objects.create(user=user),
        product=product,
        quantity=3,
    )
    client.post(
        reverse("orders:checkout"),
        checkout_payload(),
        content_type="application/json",
        **auth(user),
    )
    order = Order.objects.get(user=user)

    order.mark_as_paid()

    order.refresh_from_db()
    product.refresh_from_db()
    assert order.status == Order.Status.PAID
    assert order.stock_reduced is True
    assert product.stock == 7


def test_mark_as_paid_does_not_reduce_stock_twice(user, product):
    order = create_order(user, product)

    order.mark_as_paid()
    order.mark_as_paid()

    product.refresh_from_db()
    assert product.stock == 9


def test_mark_as_paid_fails_when_stock_is_insufficient(user, product):
    order = create_order(user, product)
    order_item = order.items.get()
    order_item.quantity = product.stock + 1
    order_item.save(update_fields=("quantity",))

    with pytest.raises(ValidationError, match="Insufficient stock"):
        order.mark_as_paid()

    order.refresh_from_db()
    product.refresh_from_db()
    assert order.status == Order.Status.PENDING
    assert order.stock_reduced is False
    assert product.stock == 10


def test_empty_cart_checkout_fails(client, user):
    response = client.post(
        reverse("orders:checkout"),
        checkout_payload(),
        content_type="application/json",
        **auth(user),
    )

    assert response.status_code == 400
    assert Order.objects.count() == 0


def test_user_sees_own_orders_only(client, user, other_user, product):
    own_order = create_order(user, product)
    create_order(other_user, product)

    response = client.get(reverse("orders:order-list"), **auth(user))

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [own_order.id]


def test_admin_sees_all_orders(client, user, other_user, admin, product):
    create_order(user, product)
    create_order(other_user, product)

    response = client.get(reverse("orders:order-list"), **auth(admin))

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_new_and_legacy_product_urls_work(client, product):
    new_response = client.get("/api/v1/products/")
    legacy_response = client.get("/api/v1/products/products/")

    assert new_response.status_code == 200
    assert legacy_response.status_code == 200
    assert new_response.json()["results"][0]["id"] == product.id
    assert legacy_response.json()["results"][0]["id"] == product.id
