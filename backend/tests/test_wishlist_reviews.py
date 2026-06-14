import pytest
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from products.models import Category, Product, ProductReview, WishlistItem

pytestmark = pytest.mark.django_db


def authorization_header(user):
    token = RefreshToken.for_user(user).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def user():
    return User.objects.create_user(
        phone_number="09121111111",
        password="StrongPassword!42",
        first_name="Sara",
        last_name="Ahmadi",
        is_active=True,
        is_phone_verified=True,
    )


@pytest.fixture
def second_user():
    return User.objects.create_user(
        phone_number="09122222222",
        password="StrongPassword!42",
        first_name="Ali",
        last_name="Karimi",
        is_active=True,
        is_phone_verified=True,
    )


@pytest.fixture
def product():
    category = Category.objects.create(name="Puzzles", slug="puzzles")
    return Product.objects.create(
        category=category,
        name="Space Puzzle",
        slug="space-puzzle",
        description="A colorful space puzzle.",
        sku="PUZZLE-SPACE-001",
        price=500000,
        stock=10,
        age_group=Product.AgeGroup.SIX_TO_EIGHT,
        gender=Product.Gender.UNISEX,
    )


def test_add_wishlist_item(client, user, product):
    response = client.post(
        reverse("products:wishlist-list"),
        {"product": product.id},
        content_type="application/json",
        **authorization_header(user),
    )

    assert response.status_code == 201
    assert WishlistItem.objects.filter(user=user, product=product).exists()
    assert response.json()["product_detail"]["slug"] == product.slug


def test_cannot_duplicate_wishlist_item(client, user, product):
    WishlistItem.objects.create(user=user, product=product)

    response = client.post(
        reverse("products:wishlist-list"),
        {"product": product.id},
        content_type="application/json",
        **authorization_header(user),
    )

    assert response.status_code == 400
    assert WishlistItem.objects.filter(user=user, product=product).count() == 1


def test_cannot_add_inactive_product_to_wishlist(client, user, product):
    product.is_active = False
    product.save(update_fields=("is_active",))

    response = client.post(
        reverse("products:wishlist-list"),
        {"product": product.id},
        content_type="application/json",
        **authorization_header(user),
    )

    assert response.status_code == 400
    assert not WishlistItem.objects.filter(user=user, product=product).exists()


def test_remove_wishlist_item(client, user, product):
    item = WishlistItem.objects.create(user=user, product=product)

    response = client.delete(
        reverse("products:wishlist-detail", args=(item.id,)),
        **authorization_header(user),
    )

    assert response.status_code == 204
    assert not WishlistItem.objects.filter(id=item.id).exists()


def test_cannot_remove_another_users_wishlist_item(
    client,
    user,
    second_user,
    product,
):
    item = WishlistItem.objects.create(user=second_user, product=product)

    response = client.delete(
        reverse("products:wishlist-detail", args=(item.id,)),
        **authorization_header(user),
    )

    assert response.status_code == 404
    assert WishlistItem.objects.filter(id=item.id).exists()


def test_create_review(client, user, product):
    response = client.post(
        reverse("products:product-reviews", args=(product.slug,)),
        {"rating": 5, "comment": "Excellent toy."},
        content_type="application/json",
        **authorization_header(user),
    )

    assert response.status_code == 201
    review = ProductReview.objects.get(user=user, product=product)
    assert review.rating == 5
    assert review.is_approved is False


def test_duplicate_review_rejected(client, user, product):
    ProductReview.objects.create(user=user, product=product, rating=4)

    response = client.post(
        reverse("products:product-reviews", args=(product.slug,)),
        {"rating": 5},
        content_type="application/json",
        **authorization_header(user),
    )

    assert response.status_code == 400
    assert ProductReview.objects.filter(user=user, product=product).count() == 1


def test_unapproved_review_is_not_public(client, user, product):
    ProductReview.objects.create(user=user, product=product, rating=4)

    response = client.get(reverse("products:product-reviews", args=(product.slug,)))

    assert response.status_code == 200
    assert response.json() == []


def test_approved_review_is_public(client, user, product):
    ProductReview.objects.create(
        user=user,
        product=product,
        rating=4,
        is_approved=True,
    )

    response = client.get(reverse("products:product-reviews", args=(product.slug,)))

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["rating"] == 4


def test_product_detail_includes_approved_review_statistics(
    client,
    user,
    second_user,
    product,
):
    ProductReview.objects.create(
        user=user,
        product=product,
        rating=5,
        is_approved=True,
    )
    ProductReview.objects.create(
        user=second_user,
        product=product,
        rating=3,
        is_approved=True,
    )

    response = client.get(reverse("products:product-detail", args=(product.slug,)))

    assert response.status_code == 200
    assert response.json()["average_rating"] == 4.0
    assert response.json()["review_count"] == 2
