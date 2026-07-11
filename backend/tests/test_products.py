import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from products.models import (
    Brand,
    Category,
    HomepageProductSlot,
    Product,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def category():
    return Category.objects.create(name="Building Toys", slug="building-toys")


@pytest.fixture
def brand():
    return Brand.objects.create(name="PlayNest", slug="playnest")


@pytest.fixture
def product(category, brand):
    return Product.objects.create(
        category=category,
        brand=brand,
        name="Color Blocks",
        slug="color-blocks",
        description="A colorful building block set.",
        sku="BLOCK-001",
        price=1000,
        discount_price=800,
        stock=5,
        age_group=Product.AgeGroup.THREE_TO_FIVE,
        gender=Product.Gender.UNISEX,
        is_featured=True,
    )


def product_payload(category, brand):
    return {
        "category": category.id,
        "brand": brand.id,
        "name": "Toy Train",
        "slug": "toy-train",
        "description": "A wooden toy train.",
        "short_description": "Wooden train",
        "sku": "TRAIN-001",
        "price": 1500,
        "discount_price": 1200,
        "stock": 10,
        "age_group": Product.AgeGroup.THREE_TO_FIVE,
        "gender": Product.Gender.UNISEX,
        "is_active": True,
        "is_featured": False,
    }


def authorization_header(user):
    return {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(user).access_token}"}


def test_list_products_allows_public_access(client, product):
    response = client.get(reverse("products:product-list"))
    data = response.json()

    assert response.status_code == 200
    assert data["count"] == 1
    assert data["next"] is None
    assert data["previous"] is None
    assert len(data["results"]) == 1
    assert data["results"][0]["name"] == product.name
    assert data["results"][0]["category"]["slug"] == product.category.slug
    assert data["results"][0]["brand"]["slug"] == product.brand.slug
    assert data["results"][0]["final_price"] == product.discount_price
    assert data["results"][0]["is_in_stock"] is True
    assert data["results"][0]["main_image"] is None


def test_product_detail_returns_simple_product_fields(client, product):
    response = client.get(reverse("products:product-detail", args=(product.slug,)))
    data = response.json()

    assert response.status_code == 200
    assert data["name"] == product.name
    assert data["final_price"] == product.discount_price
    assert "options" not in data
    assert "has_options" not in data


def test_create_product_requires_admin(client, category, brand):
    response = client.post(
        reverse("products:product-list"),
        product_payload(category, brand),
        content_type="application/json",
    )

    assert response.status_code in (401, 403)
    assert Product.objects.count() == 0


def test_admin_can_create_product(client, category, brand):
    admin = User.objects.create_superuser(
        phone_number="09123456789",
        password="StrongPassword!42",
    )

    response = client.post(
        reverse("products:product-list"),
        product_payload(category, brand),
        content_type="application/json",
        **authorization_header(admin),
    )

    assert response.status_code == 201
    assert Product.objects.filter(sku="TRAIN-001").exists()


def test_discount_price_validation(category, brand):
    product = Product(
        category=category,
        brand=brand,
        name="Invalid Toy",
        slug="invalid-toy",
        description="Invalid discount.",
        sku="INVALID-001",
        price=1000,
        discount_price=1000,
        stock=1,
        age_group=Product.AgeGroup.SIX_TO_EIGHT,
        gender=Product.Gender.UNISEX,
    )

    with pytest.raises(ValidationError):
        product.full_clean()


def test_product_final_price(category, brand):
    product = Product(
        category=category,
        brand=brand,
        name="Discount Toy",
        slug="discount-toy",
        description="Discounted toy.",
        sku="DISCOUNT-001",
        price=1000,
        discount_price=750,
        stock=1,
        age_group=Product.AgeGroup.SIX_TO_EIGHT,
        gender=Product.Gender.UNISEX,
    )

    assert product.final_price == 750
    product.discount_price = None
    assert product.final_price == 1000


def test_product_is_in_stock(category, brand):
    product = Product(
        category=category,
        brand=brand,
        name="Stock Toy",
        slug="stock-toy",
        description="Stock test toy.",
        sku="STOCK-001",
        price=1000,
        stock=1,
        age_group=Product.AgeGroup.SIX_TO_EIGHT,
        gender=Product.Gender.UNISEX,
    )

    assert product.is_in_stock is True
    product.stock = 0
    assert product.is_in_stock is False


def test_product_list_filtering_search_and_ordering(client, product, category, brand):
    Product.objects.create(
        category=category,
        brand=brand,
        name="Wooden Puzzle",
        slug="wooden-puzzle",
        description="A simple puzzle.",
        sku="PUZZLE-001",
        price=500,
        stock=0,
        age_group=Product.AgeGroup.SIX_TO_EIGHT,
        gender=Product.Gender.GIRL,
    )

    filtered_response = client.get(
        reverse("products:product-list"),
        {
            "category": category.id,
            "brand": brand.id,
            "age_group": Product.AgeGroup.THREE_TO_FIVE,
            "gender": Product.Gender.UNISEX,
            "is_featured": True,
            "min_price": 750,
            "max_price": 850,
            "in_stock": True,
            "search": "Color BLOCK-001",
        },
    )
    ordered_response = client.get(
        reverse("products:product-list"),
        {"ordering": "price"},
    )

    assert filtered_response.status_code == 200
    assert [item["sku"] for item in filtered_response.json()["results"]] == [
        product.sku
    ]
    assert [item["sku"] for item in ordered_response.json()["results"]] == [
        "PUZZLE-001",
        product.sku,
    ]


def test_product_list_is_paginated(client, category, brand):
    for index in range(13):
        Product.objects.create(
            category=category,
            brand=brand,
            name=f"Puzzle {index}",
            slug=f"puzzle-{index}",
            description="A scalable product list item.",
            sku=f"PUZZLE-{index:03}",
            price=1000 + index,
            stock=5,
            age_group=Product.AgeGroup.SIX_TO_EIGHT,
            gender=Product.Gender.UNISEX,
        )

    first_page = client.get(reverse("products:product-list"), {"page": 1})
    second_page = client.get(reverse("products:product-list"), {"page": 2})

    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert first_page.json()["count"] == 13
    assert len(first_page.json()["results"]) == 12
    assert len(second_page.json()["results"]) == 1
    assert first_page.json()["next"] is not None
    assert second_page.json()["previous"] is not None


def test_product_list_pagination_respects_filters(client, category, brand):
    other_category = Category.objects.create(name="Card Games", slug="card-games")
    for index in range(14):
        Product.objects.create(
            category=category if index < 13 else other_category,
            brand=brand,
            name=f"Filtered Game {index}",
            slug=f"filtered-game-{index}",
            description="Filter pagination test.",
            sku=f"FILTER-{index:03}",
            price=2000 + index,
            stock=5,
            age_group=Product.AgeGroup.TWELVE_PLUS,
            gender=Product.Gender.UNISEX,
        )

    response = client.get(
        reverse("products:product-list"),
        {"category": category.id, "page": 2},
    )

    assert response.status_code == 200
    assert response.json()["count"] == 13
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["category"]["id"] == category.id


def test_homepage_sections_endpoint_groups_active_slots(
    client, product, category, brand
):
    second_product = Product.objects.create(
        category=category,
        brand=brand,
        name="Strategy Game",
        slug="strategy-game",
        description="A strategic board game.",
        sku="STRATEGY-001",
        price=2500,
        stock=3,
        age_group=Product.AgeGroup.TWELVE_PLUS,
        gender=Product.Gender.UNISEX,
    )
    HomepageProductSlot.objects.create(
        section=HomepageProductSlot.Section.HERO_SLIDER,
        product=product,
        sort_order=2,
        title_override="Hero title",
    )
    HomepageProductSlot.objects.create(
        section=HomepageProductSlot.Section.HERO_SLIDER,
        product=second_product,
        sort_order=1,
    )
    HomepageProductSlot.objects.create(
        section=HomepageProductSlot.Section.POPULAR_MARQUEE,
        product=product,
        sort_order=1,
    )
    HomepageProductSlot.objects.create(
        section=HomepageProductSlot.Section.FEATURED_PRODUCTS,
        product=second_product,
        sort_order=1,
    )

    response = client.get(reverse("products:homepage-sections"))

    assert response.status_code == 200
    data = response.json()
    assert set(data) == {
        "hero_slider",
        "popular_marquee",
        "latest_carousel",
        "featured_products",
    }
    assert [item["product"]["slug"] for item in data["hero_slider"]] == [
        second_product.slug,
        product.slug,
    ]
    assert data["hero_slider"][1]["title_override"] == "Hero title"
    assert data["popular_marquee"][0]["product"]["slug"] == product.slug
    assert data["latest_carousel"] == []
    assert data["featured_products"][0]["product"]["slug"] == second_product.slug


def test_homepage_sections_endpoint_ignores_inactive_slots(client, product):
    other_product = Product.objects.create(
        category=product.category,
        brand=product.brand,
        name="Active Featured Game",
        slug="active-featured-game",
        description="An active selected product.",
        sku="ACTIVE-FEATURED-001",
        price=2000,
        stock=4,
        age_group=Product.AgeGroup.SIX_TO_EIGHT,
        gender=Product.Gender.UNISEX,
    )
    HomepageProductSlot.objects.create(
        section=HomepageProductSlot.Section.FEATURED_PRODUCTS,
        product=product,
        sort_order=1,
        is_active=False,
    )
    HomepageProductSlot.objects.create(
        section=HomepageProductSlot.Section.FEATURED_PRODUCTS,
        product=other_product,
        sort_order=2,
    )

    response = client.get(reverse("products:homepage-sections"))

    assert response.status_code == 200
    featured_slugs = [
        item["product"]["slug"] for item in response.json()["featured_products"]
    ]
    assert featured_slugs == [other_product.slug]


def test_homepage_sections_endpoint_returns_admin_selected_popular_and_featured(
    client, product, category, brand
):
    popular_product = Product.objects.create(
        category=category,
        brand=brand,
        name="Popular Game",
        slug="popular-game",
        description="Popular game.",
        sku="POPULAR-001",
        price=3200,
        stock=5,
        age_group=Product.AgeGroup.TWELVE_PLUS,
        gender=Product.Gender.UNISEX,
    )
    featured_product = Product.objects.create(
        category=category,
        brand=brand,
        name="Featured Game",
        slug="featured-game",
        description="Featured game.",
        sku="FEATURED-001",
        price=4500,
        stock=5,
        age_group=Product.AgeGroup.TWELVE_PLUS,
        gender=Product.Gender.UNISEX,
    )
    HomepageProductSlot.objects.create(
        section=HomepageProductSlot.Section.POPULAR_MARQUEE,
        product=popular_product,
        sort_order=2,
    )
    HomepageProductSlot.objects.create(
        section=HomepageProductSlot.Section.POPULAR_MARQUEE,
        product=product,
        sort_order=1,
    )
    HomepageProductSlot.objects.create(
        section=HomepageProductSlot.Section.FEATURED_PRODUCTS,
        product=featured_product,
        sort_order=1,
    )

    response = client.get(reverse("products:homepage-sections"))

    assert response.status_code == 200
    data = response.json()
    assert [item["product"]["slug"] for item in data["popular_marquee"]] == [
        product.slug,
        popular_product.slug,
    ]
    assert [item["product"]["slug"] for item in data["featured_products"]] == [
        featured_product.slug,
    ]


def test_homepage_sections_endpoint_ignores_inactive_products(
    client, product, category, brand
):
    inactive_product = Product.objects.create(
        category=category,
        brand=brand,
        name="Inactive Popular Game",
        slug="inactive-popular-game",
        description="Inactive product.",
        sku="INACTIVE-POPULAR-001",
        price=2000,
        stock=5,
        age_group=Product.AgeGroup.SIX_TO_EIGHT,
        gender=Product.Gender.UNISEX,
        is_active=False,
    )
    HomepageProductSlot.objects.create(
        section=HomepageProductSlot.Section.POPULAR_MARQUEE,
        product=inactive_product,
        sort_order=1,
    )

    response = client.get(reverse("products:homepage-sections"))

    assert response.status_code == 200
    popular_slugs = [
        item["product"]["slug"] for item in response.json()["popular_marquee"]
    ]
    assert inactive_product.slug not in popular_slugs


def test_homepage_sections_endpoint_fallbacks_are_limited(client, category, brand):
    for index in range(15):
        Product.objects.create(
            category=category,
            brand=brand,
            name=f"Fallback Game {index}",
            slug=f"fallback-game-{index}",
            description="Fallback product.",
            sku=f"FALLBACK-{index:03}",
            price=1000 + index,
            stock=5,
            age_group=Product.AgeGroup.SIX_TO_EIGHT,
            gender=Product.Gender.UNISEX,
        )

    response = client.get(reverse("products:homepage-sections"))

    assert response.status_code == 200
    data = response.json()
    assert len(data["popular_marquee"]) == 12
    assert len(data["featured_products"]) == 8
    assert data["latest_carousel"] == []
