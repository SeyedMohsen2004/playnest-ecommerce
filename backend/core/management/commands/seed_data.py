from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from orders.models import Coupon
from products.models import Brand, Category, Product, ProductImage


CATEGORIES = (
    ("بردگیم", "board-games"),
    ("بازی فکری", "mind-games"),
    ("پازل", "puzzles"),
    ("لگو و ساختنی", "building-games"),
    ("بازی آموزشی", "educational-games"),
    ("بازی خانوادگی", "family-games"),
    ("بازی کارتی", "card-games"),
)

BRANDS = (
    ("IpakToys", "ipaktoys"),
    ("LEGO", "lego"),
    ("Hasbro", "hasbro"),
    ("Ravensburger", "ravensburger"),
    ("MindWare", "mindware"),
)

PRODUCTS = (
    {
        "name": "LEGO Classic Creative Bricks",
        "slug": "lego-classic-creative-bricks",
        "category": "building-games",
        "brand": "lego",
        "sku": "LEGO-CLASSIC-001",
        "price": 2_450_000,
        "discount_price": 2_190_000,
        "stock": 18,
        "age_group": Product.AgeGroup.SIX_TO_EIGHT,
        "is_featured": True,
    },
    {
        "name": "LEGO Family Build Challenge",
        "slug": "lego-family-build-challenge",
        "category": "building-games",
        "brand": "lego",
        "sku": "LEGO-FAMILY-002",
        "price": 3_900_000,
        "stock": 10,
        "age_group": Product.AgeGroup.NINE_TO_TWELVE,
        "is_featured": True,
    },
    {
        "name": "IpakToys Magnetic Building Challenge",
        "slug": "ipaktoys-magnetic-building-challenge",
        "category": "building-games",
        "brand": "ipaktoys",
        "sku": "IPAK-MAG-064",
        "price": 1_850_000,
        "discount_price": 1_650_000,
        "stock": 25,
        "age_group": Product.AgeGroup.THREE_TO_FIVE,
        "is_featured": True,
    },
    {
        "name": "IpakToys Wooden Pattern Blocks",
        "slug": "ipaktoys-wooden-pattern-blocks",
        "category": "building-games",
        "brand": "ipaktoys",
        "sku": "IPAK-WOOD-050",
        "price": 980_000,
        "stock": 30,
        "age_group": Product.AgeGroup.THREE_TO_FIVE,
        "is_featured": False,
    },
    {
        "name": "Hasbro Monopoly Classic",
        "slug": "hasbro-monopoly-classic",
        "category": "board-games",
        "brand": "hasbro",
        "sku": "HAS-MONO-001",
        "price": 1_490_000,
        "stock": 18,
        "age_group": Product.AgeGroup.TWELVE_PLUS,
        "is_featured": True,
    },
    {
        "name": "IpakToys Strategy Family Board Game",
        "slug": "ipaktoys-strategy-family-board-game",
        "category": "board-games",
        "brand": "ipaktoys",
        "sku": "IPAK-BOARD-001",
        "price": 1_250_000,
        "stock": 17,
        "age_group": Product.AgeGroup.NINE_TO_TWELVE,
        "is_featured": True,
    },
    {
        "name": "IpakToys Family Deduction Night",
        "slug": "ipaktoys-family-deduction-night",
        "category": "family-games",
        "brand": "ipaktoys",
        "sku": "IPAK-FAMILY-001",
        "price": 1_320_000,
        "discount_price": 1_180_000,
        "stock": 14,
        "age_group": Product.AgeGroup.TWELVE_PLUS,
        "is_featured": True,
    },
    {
        "name": "IpakToys Group Party Challenge",
        "slug": "ipaktoys-group-party-challenge",
        "category": "family-games",
        "brand": "ipaktoys",
        "sku": "IPAK-PARTY-001",
        "price": 890_000,
        "stock": 35,
        "age_group": Product.AgeGroup.TWELVE_PLUS,
        "is_featured": False,
    },
    {
        "name": "MindWare Junior Mind Challenge",
        "slug": "mindware-junior-mind-challenge",
        "category": "mind-games",
        "brand": "mindware",
        "sku": "MW-MIND-001",
        "price": 940_000,
        "discount_price": 840_000,
        "stock": 22,
        "age_group": Product.AgeGroup.SIX_TO_EIGHT,
        "is_featured": True,
    },
    {
        "name": "IpakToys Logic Maze Junior",
        "slug": "ipaktoys-logic-maze-junior",
        "category": "mind-games",
        "brand": "ipaktoys",
        "sku": "IPAK-LOGIC-001",
        "price": 760_000,
        "stock": 24,
        "age_group": Product.AgeGroup.SIX_TO_EIGHT,
        "is_featured": False,
    },
    {
        "name": "IpakToys Memory Match Persian",
        "slug": "ipaktoys-memory-match-persian",
        "category": "mind-games",
        "brand": "ipaktoys",
        "sku": "IPAK-MEMORY-001",
        "price": 520_000,
        "stock": 40,
        "age_group": Product.AgeGroup.THREE_TO_FIVE,
        "is_featured": False,
    },
    {
        "name": "MindWare Brain Teaser Box",
        "slug": "mindware-brain-teaser-box",
        "category": "mind-games",
        "brand": "mindware",
        "sku": "MW-BRAIN-001",
        "price": 1_100_000,
        "stock": 16,
        "age_group": Product.AgeGroup.NINE_TO_TWELVE,
        "is_featured": True,
    },
    {
        "name": "Ravensburger World Map Puzzle",
        "slug": "ravensburger-world-map-puzzle",
        "category": "puzzles",
        "brand": "ravensburger",
        "sku": "RAV-PUZZLE-MAP",
        "price": 650_000,
        "discount_price": 590_000,
        "stock": 28,
        "age_group": Product.AgeGroup.SIX_TO_EIGHT,
        "is_featured": False,
    },
    {
        "name": "Ravensburger City Landmark Puzzle 500",
        "slug": "ravensburger-city-landmark-puzzle-500",
        "category": "puzzles",
        "brand": "ravensburger",
        "sku": "RAV-PUZZLE-500",
        "price": 890_000,
        "stock": 19,
        "age_group": Product.AgeGroup.TWELVE_PLUS,
        "is_featured": True,
    },
    {
        "name": "IpakToys Animals Puzzle Kids",
        "slug": "ipaktoys-animals-puzzle-kids",
        "category": "puzzles",
        "brand": "ipaktoys",
        "sku": "IPAK-PUZZLE-KIDS",
        "price": 430_000,
        "stock": 32,
        "age_group": Product.AgeGroup.THREE_TO_FIVE,
        "is_featured": False,
    },
    {
        "name": "IpakToys Persian Word Card Game",
        "slug": "ipaktoys-persian-word-card-game",
        "category": "card-games",
        "brand": "ipaktoys",
        "sku": "IPAK-CARD-WORD",
        "price": 520_000,
        "stock": 38,
        "age_group": Product.AgeGroup.NINE_TO_TWELVE,
        "is_featured": True,
    },
    {
        "name": "IpakToys Quick Math Card Game",
        "slug": "ipaktoys-quick-math-card-game",
        "category": "card-games",
        "brand": "ipaktoys",
        "sku": "IPAK-CARD-MATH",
        "price": 480_000,
        "discount_price": 420_000,
        "stock": 34,
        "age_group": Product.AgeGroup.SIX_TO_EIGHT,
        "is_featured": False,
    },
    {
        "name": "IpakToys Family Story Card Game",
        "slug": "ipaktoys-family-story-card-game",
        "category": "card-games",
        "brand": "ipaktoys",
        "sku": "IPAK-CARD-STORY",
        "price": 590_000,
        "stock": 27,
        "age_group": Product.AgeGroup.NINE_TO_TWELVE,
        "is_featured": False,
    },
    {
        "name": "IpakToys Educational Science Quiz",
        "slug": "ipaktoys-educational-science-quiz",
        "category": "educational-games",
        "brand": "ipaktoys",
        "sku": "IPAK-EDU-SCIENCE",
        "price": 690_000,
        "stock": 26,
        "age_group": Product.AgeGroup.NINE_TO_TWELVE,
        "is_featured": True,
    },
    {
        "name": "IpakToys Alphabet Learning Game",
        "slug": "ipaktoys-alphabet-learning-game",
        "category": "educational-games",
        "brand": "ipaktoys",
        "sku": "IPAK-EDU-ABC",
        "price": 390_000,
        "stock": 50,
        "age_group": Product.AgeGroup.THREE_TO_FIVE,
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
        "code": "GAME50000",
        "discount_type": Coupon.DiscountType.FIXED,
        "discount_value": 50_000,
        "max_discount_amount": None,
        "min_order_amount": 300_000,
        "usage_limit": None,
        "is_active": True,
    },
)

OLD_SEED_CATEGORY_SLUGS = (
    "building-toys",
    "dolls",
    "toy-cars",
    "educational",
    "baby-toddler",
)

OLD_SEED_PRODUCT_SLUGS = (
    "lego-city-fire-station",
    "playnest-magnetic-tiles-64",
    "playnest-wooden-building-blocks",
    "barbie-dream-fashion-doll",
    "playnest-soft-baby-doll",
    "hasbro-my-little-pony-set",
    "hot-wheels-mega-track",
    "playnest-metal-car-collection",
    "playnest-remote-control-racer",
    "playnest-persian-alphabet-cards",
    "fisher-price-learning-laptop",
    "playnest-junior-science-lab",
    "playnest-world-map-puzzle",
    "playnest-strategy-board-game",
    "fisher-price-musical-activity-gym",
    "fisher-price-stack-roll-cups",
    "playnest-baby-sensory-ball-set",
    "playnest-shape-sorter-house",
)


def placeholder_svg(product_name):
    safe_name = (
        product_name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">'
        '<rect width="100%" height="100%" fill="#fff7ed"/>'
        '<circle cx="400" cy="230" r="95" fill="#fb7185"/>'
        '<rect x="240" y="330" width="320" height="70" rx="24" fill="#fbbf24"/>'
        '<text x="400" y="470" font-family="Arial" font-size="28" '
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
        self.deactivate_old_seed_content()

        self.stdout.write(
            self.style.WARNING(
                "FREESHIP was skipped because coupons only support percentage "
                "and fixed discounts."
            )
        )
        self.stdout.write(
            self.style.SUCCESS("IpakToys development seed data is ready.")
        )

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
                    "description": f"IpakToys {name} collection",
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
                    "description": f"{name} products available from IpakToys",
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
                    f"{data['name']} is selected for the IpakToys development "
                    "catalog of board games, puzzles, and creative games."
                ),
                "short_description": f"Shop {data['name']} at IpakToys.",
                "sku": data["sku"],
                "price": data["price"],
                "discount_price": data.get("discount_price"),
                "stock": data["stock"],
                "age_group": data["age_group"],
                "gender": Product.Gender.UNISEX,
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

        Coupon.objects.filter(code="TOY50000").update(is_active=False)

    def deactivate_old_seed_content(self):
        Product.objects.filter(slug__in=OLD_SEED_PRODUCT_SLUGS).update(
            is_active=False,
            is_featured=False,
        )
        Category.objects.filter(slug__in=OLD_SEED_CATEGORY_SLUGS).update(
            is_active=False
        )
