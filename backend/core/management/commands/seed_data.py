from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from orders.models import Coupon
from products.models import Brand, Category, Product, ProductImage


CATEGORIES = (
    ("لگو و ساختنی", "building-toys"),
    ("عروسک", "dolls"),
    ("ماشین اسباب‌بازی", "toy-cars"),
    ("آموزشی", "educational"),
    ("فکری و پازل", "puzzles"),
    ("نوزاد و خردسال", "baby-toddler"),
)

BRANDS = (
    ("LEGO", "lego"),
    ("Mattel", "mattel"),
    ("Hasbro", "hasbro"),
    ("Fisher Price", "fisher-price"),
    ("PlayNest", "playnest"),
)

PRODUCTS = (
    {
        "name": "LEGO Classic Creative Bricks",
        "slug": "lego-classic-creative-bricks",
        "category": "building-toys",
        "brand": "lego",
        "sku": "LEGO-CLASSIC-001",
        "price": 2_450_000,
        "discount_price": 2_190_000,
        "stock": 18,
        "age_group": Product.AgeGroup.SIX_TO_EIGHT,
        "gender": Product.Gender.UNISEX,
        "is_featured": True,
    },
    {
        "name": "LEGO City Fire Station",
        "slug": "lego-city-fire-station",
        "category": "building-toys",
        "brand": "lego",
        "sku": "LEGO-CITY-002",
        "price": 4_900_000,
        "stock": 9,
        "age_group": Product.AgeGroup.NINE_TO_TWELVE,
        "gender": Product.Gender.UNISEX,
        "is_featured": True,
    },
    {
        "name": "PlayNest Magnetic Tiles 64 Piece",
        "slug": "playnest-magnetic-tiles-64",
        "category": "building-toys",
        "brand": "playnest",
        "sku": "PN-MAG-064",
        "price": 1_850_000,
        "discount_price": 1_650_000,
        "stock": 25,
        "age_group": Product.AgeGroup.THREE_TO_FIVE,
        "gender": Product.Gender.UNISEX,
        "is_featured": True,
    },
    {
        "name": "PlayNest Wooden Building Blocks",
        "slug": "playnest-wooden-building-blocks",
        "category": "building-toys",
        "brand": "playnest",
        "sku": "PN-WOOD-050",
        "price": 980_000,
        "stock": 30,
        "age_group": Product.AgeGroup.THREE_TO_FIVE,
        "gender": Product.Gender.UNISEX,
        "is_featured": False,
    },
    {
        "name": "Barbie Dream Fashion Doll",
        "slug": "barbie-dream-fashion-doll",
        "category": "dolls",
        "brand": "mattel",
        "sku": "MAT-BARBIE-001",
        "price": 1_750_000,
        "discount_price": 1_590_000,
        "stock": 14,
        "age_group": Product.AgeGroup.SIX_TO_EIGHT,
        "gender": Product.Gender.GIRL,
        "is_featured": True,
    },
    {
        "name": "PlayNest Soft Baby Doll",
        "slug": "playnest-soft-baby-doll",
        "category": "dolls",
        "brand": "playnest",
        "sku": "PN-DOLL-001",
        "price": 720_000,
        "stock": 22,
        "age_group": Product.AgeGroup.THREE_TO_FIVE,
        "gender": Product.Gender.GIRL,
        "is_featured": False,
    },
    {
        "name": "Hasbro My Little Pony Set",
        "slug": "hasbro-my-little-pony-set",
        "category": "dolls",
        "brand": "hasbro",
        "sku": "HAS-PONY-003",
        "price": 1_320_000,
        "stock": 16,
        "age_group": Product.AgeGroup.THREE_TO_FIVE,
        "gender": Product.Gender.GIRL,
        "is_featured": False,
    },
    {
        "name": "Hot Wheels Mega Track",
        "slug": "hot-wheels-mega-track",
        "category": "toy-cars",
        "brand": "mattel",
        "sku": "MAT-HW-TRACK",
        "price": 2_890_000,
        "discount_price": 2_600_000,
        "stock": 11,
        "age_group": Product.AgeGroup.SIX_TO_EIGHT,
        "gender": Product.Gender.BOY,
        "is_featured": True,
    },
    {
        "name": "PlayNest Metal Car Collection",
        "slug": "playnest-metal-car-collection",
        "category": "toy-cars",
        "brand": "playnest",
        "sku": "PN-CAR-010",
        "price": 890_000,
        "stock": 35,
        "age_group": Product.AgeGroup.THREE_TO_FIVE,
        "gender": Product.Gender.BOY,
        "is_featured": False,
    },
    {
        "name": "PlayNest Remote Control Racer",
        "slug": "playnest-remote-control-racer",
        "category": "toy-cars",
        "brand": "playnest",
        "sku": "PN-RC-001",
        "price": 2_150_000,
        "stock": 12,
        "age_group": Product.AgeGroup.NINE_TO_TWELVE,
        "gender": Product.Gender.BOY,
        "is_featured": True,
    },
    {
        "name": "PlayNest Persian Alphabet Cards",
        "slug": "playnest-persian-alphabet-cards",
        "category": "educational",
        "brand": "playnest",
        "sku": "PN-EDU-ABC",
        "price": 390_000,
        "stock": 50,
        "age_group": Product.AgeGroup.THREE_TO_FIVE,
        "gender": Product.Gender.UNISEX,
        "is_featured": False,
    },
    {
        "name": "Fisher Price Learning Laptop",
        "slug": "fisher-price-learning-laptop",
        "category": "educational",
        "brand": "fisher-price",
        "sku": "FP-LAPTOP-01",
        "price": 1_680_000,
        "discount_price": 1_490_000,
        "stock": 15,
        "age_group": Product.AgeGroup.THREE_TO_FIVE,
        "gender": Product.Gender.UNISEX,
        "is_featured": True,
    },
    {
        "name": "PlayNest Junior Science Lab",
        "slug": "playnest-junior-science-lab",
        "category": "educational",
        "brand": "playnest",
        "sku": "PN-SCIENCE-01",
        "price": 1_250_000,
        "stock": 20,
        "age_group": Product.AgeGroup.NINE_TO_TWELVE,
        "gender": Product.Gender.UNISEX,
        "is_featured": False,
    },
    {
        "name": "Hasbro Monopoly Classic",
        "slug": "hasbro-monopoly-classic",
        "category": "puzzles",
        "brand": "hasbro",
        "sku": "HAS-MONO-001",
        "price": 1_490_000,
        "stock": 18,
        "age_group": Product.AgeGroup.TWELVE_PLUS,
        "gender": Product.Gender.UNISEX,
        "is_featured": True,
    },
    {
        "name": "PlayNest World Map Puzzle",
        "slug": "playnest-world-map-puzzle",
        "category": "puzzles",
        "brand": "playnest",
        "sku": "PN-PUZZLE-MAP",
        "price": 650_000,
        "discount_price": 590_000,
        "stock": 28,
        "age_group": Product.AgeGroup.SIX_TO_EIGHT,
        "gender": Product.Gender.UNISEX,
        "is_featured": False,
    },
    {
        "name": "PlayNest Strategy Board Game",
        "slug": "playnest-strategy-board-game",
        "category": "puzzles",
        "brand": "playnest",
        "sku": "PN-BOARD-001",
        "price": 1_100_000,
        "stock": 17,
        "age_group": Product.AgeGroup.NINE_TO_TWELVE,
        "gender": Product.Gender.UNISEX,
        "is_featured": True,
    },
    {
        "name": "Fisher Price Musical Activity Gym",
        "slug": "fisher-price-musical-activity-gym",
        "category": "baby-toddler",
        "brand": "fisher-price",
        "sku": "FP-GYM-001",
        "price": 2_350_000,
        "stock": 10,
        "age_group": Product.AgeGroup.ZERO_TO_TWO,
        "gender": Product.Gender.UNISEX,
        "is_featured": True,
    },
    {
        "name": "Fisher Price Stack and Roll Cups",
        "slug": "fisher-price-stack-roll-cups",
        "category": "baby-toddler",
        "brand": "fisher-price",
        "sku": "FP-CUPS-001",
        "price": 580_000,
        "stock": 32,
        "age_group": Product.AgeGroup.ZERO_TO_TWO,
        "gender": Product.Gender.UNISEX,
        "is_featured": False,
    },
    {
        "name": "PlayNest Baby Sensory Ball Set",
        "slug": "playnest-baby-sensory-ball-set",
        "category": "baby-toddler",
        "brand": "playnest",
        "sku": "PN-BABY-BALL",
        "price": 490_000,
        "discount_price": 450_000,
        "stock": 40,
        "age_group": Product.AgeGroup.ZERO_TO_TWO,
        "gender": Product.Gender.UNISEX,
        "is_featured": False,
    },
    {
        "name": "PlayNest Shape Sorter House",
        "slug": "playnest-shape-sorter-house",
        "category": "baby-toddler",
        "brand": "playnest",
        "sku": "PN-SHAPE-001",
        "price": 760_000,
        "stock": 24,
        "age_group": Product.AgeGroup.ZERO_TO_TWO,
        "gender": Product.Gender.UNISEX,
        "is_featured": False,
    },
)

COUPONS = (
    {
        "code": "OFF10",
        "discount_type": Coupon.DiscountType.PERCENTAGE,
        "discount_value": 10,
        "max_discount_amount": 500_000,
        "min_order_amount": 500_000,
        "usage_limit": None,
        "is_active": True,
    },
    {
        "code": "TOY50000",
        "discount_type": Coupon.DiscountType.FIXED,
        "discount_value": 50_000,
        "max_discount_amount": None,
        "min_order_amount": 300_000,
        "usage_limit": None,
        "is_active": True,
    },
)


def placeholder_svg(product_name):
    safe_name = (
        product_name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">'
        '<rect width="100%" height="100%" fill="#f3f4f6"/>'
        '<circle cx="400" cy="245" r="90" fill="#f59e0b"/>'
        '<text x="400" y="390" font-family="Arial" font-size="30" '
        f'text-anchor="middle" fill="#1f2937">{safe_name}</text>'
        "</svg>"
    )


class Command(BaseCommand):
    help = "Create idempotent development users, catalog products, and coupons."

    @transaction.atomic
    def handle(self, *args, **options):
        self.seed_users()
        categories = self.seed_categories()
        brands = self.seed_brands()
        self.seed_products(categories, brands)
        self.seed_coupons()

        self.stdout.write(
            self.style.WARNING(
                "FREESHIP was skipped because coupons only support percentage "
                "and fixed discounts."
            )
        )
        self.stdout.write(self.style.SUCCESS("Development seed data is ready."))

    def seed_users(self):
        users = (
            (
                "09120000000",
                "AdminPass123!",
                {
                    "first_name": "Admin",
                    "last_name": "User",
                    "is_staff": True,
                    "is_superuser": True,
                    "is_active": True,
                    "is_phone_verified": True,
                },
            ),
            (
                "09121111111",
                "CustomerPass123!",
                {
                    "first_name": "Test",
                    "last_name": "Customer",
                    "is_staff": False,
                    "is_superuser": False,
                    "is_active": True,
                    "is_phone_verified": True,
                },
            ),
        )
        for phone_number, password, defaults in users:
            user, _ = User.objects.update_or_create(
                phone_number=phone_number,
                defaults=defaults,
            )
            if not user.check_password(password):
                user.set_password(password)
                user.save(update_fields=("password",))

    def seed_categories(self):
        categories = {}
        for name, slug in CATEGORIES:
            category, _ = Category.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "description": f"PlayNest {name} collection",
                    "is_active": True,
                },
            )
            categories[slug] = category
        return categories

    def seed_brands(self):
        brands = {}
        for name, slug in BRANDS:
            brand, _ = Brand.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "description": f"{name} toys available from PlayNest",
                    "is_active": True,
                },
            )
            brands[slug] = brand
        return brands

    def seed_products(self, categories, brands):
        for data in PRODUCTS:
            defaults = {
                "name": data["name"],
                "category": categories[data["category"]],
                "brand": brands[data["brand"]],
                "description": (
                    f"{data['name']} is a quality toy selected for the PlayNest "
                    "development catalog."
                ),
                "short_description": f"Shop {data['name']} at PlayNest.",
                "sku": data["sku"],
                "price": data["price"],
                "discount_price": data.get("discount_price"),
                "stock": data["stock"],
                "age_group": data["age_group"],
                "gender": data["gender"],
                "is_active": True,
                "is_featured": data["is_featured"],
            }
            product, _ = Product.objects.update_or_create(
                slug=data["slug"],
                defaults=defaults,
            )
            if not product.images.exists():
                image = ProductImage(
                    product=product,
                    alt_text=f"Placeholder for {product.name}",
                    is_main=True,
                )
                image.image.save(
                    f"seed/{product.slug}.svg",
                    ContentFile(placeholder_svg(product.name).encode()),
                    save=True,
                )

    def seed_coupons(self):
        for data in COUPONS:
            defaults = data.copy()
            code = defaults.pop("code")
            Coupon.objects.update_or_create(code=code, defaults=defaults)
