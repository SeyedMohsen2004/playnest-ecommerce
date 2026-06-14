import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from products.models import Brand, Category, Product

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

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == product.name
    assert response.json()[0]["category"]["slug"] == product.category.slug
    assert response.json()[0]["brand"]["slug"] == product.brand.slug
    assert response.json()[0]["final_price"] == product.discount_price
    assert response.json()[0]["is_in_stock"] is True
    assert response.json()[0]["main_image"] is None


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
    assert [item["sku"] for item in filtered_response.json()] == [product.sku]
    assert [item["sku"] for item in ordered_response.json()] == [
        "PUZZLE-001",
        product.sku,
    ]
