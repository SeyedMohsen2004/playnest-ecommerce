from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q


class Category(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="children",
        blank=True,
        null=True,
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Product(models.Model):
    class AgeGroup(models.TextChoices):
        ZERO_TO_TWO = "0_2", "0-2 years"
        THREE_TO_FIVE = "3_5", "3-5 years"
        SIX_TO_EIGHT = "6_8", "6-8 years"
        NINE_TO_TWELVE = "9_12", "9-12 years"
        TWELVE_PLUS = "12_plus", "12+ years"

    class Gender(models.TextChoices):
        UNISEX = "unisex", "Unisex"
        BOY = "boy", "Boy"
        GIRL = "girl", "Girl"

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        related_name="products",
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=275, unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=500, blank=True)
    sku = models.CharField(max_length=100, unique=True)
    price = models.PositiveIntegerField()
    discount_price = models.PositiveIntegerField(blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    age_group = models.CharField(max_length=20, choices=AgeGroup.choices)
    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        default=Gender.UNISEX,
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(
                condition=Q(discount_price__isnull=True)
                | Q(discount_price__lt=F("price")),
                name="product_discount_less_than_price",
            )
        ]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.discount_price is not None and self.discount_price >= self.price:
            raise ValidationError(
                {"discount_price": "Discount price must be less than price."}
            )

    @property
    def final_price(self):
        return self.discount_price if self.discount_price is not None else self.price

    @property
    def is_in_stock(self):
        return self.stock > 0


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=255, blank=True)
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-is_main", "created_at")

    def __str__(self):
        return self.alt_text or f"Image for {self.product}"


class ProductOption(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="options",
    )
    name = models.CharField(max_length=100)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("product", "name"),
                name="unique_product_option_name",
            )
        ]

    def __str__(self):
        return f"{self.product} - {self.name}"


class ProductOptionValue(models.Model):
    option = models.ForeignKey(
        ProductOption,
        on_delete=models.CASCADE,
        related_name="values",
    )
    value = models.CharField(max_length=100)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("option__sort_order", "sort_order", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("option", "value"),
                name="unique_product_option_value",
            )
        ]

    def __str__(self):
        return f"{self.option.name}: {self.value}"


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
    )
    option_values = models.ManyToManyField(
        ProductOptionValue,
        related_name="variants",
    )
    sku = models.CharField(max_length=100, blank=True)
    price = models.PositiveIntegerField()
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/variants/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("sku",),
                condition=~Q(sku=""),
                name="unique_non_blank_product_variant_sku",
            )
        ]

    def __str__(self):
        return f"{self.product} - {self.selected_options_label or self.sku or self.pk}"

    def clean(self):
        super().clean()
        if not self.pk:
            return

        values = list(self.option_values.select_related("option"))
        errors = validate_variant_option_values(self.product, values)
        if errors:
            raise ValidationError(errors)

        value_ids = sorted(value.id for value in values)
        duplicate_variants = (
            ProductVariant.objects.filter(product=self.product)
            .exclude(pk=self.pk)
            .prefetch_related("option_values")
        )
        for variant in duplicate_variants:
            if sorted(variant.option_values.values_list("id", flat=True)) == value_ids:
                raise ValidationError(
                    {"option_values": "This variant combination already exists."}
                )

    @property
    def is_available(self):
        return self.is_active and self.stock > 0

    @property
    def selected_options_label(self):
        values = self.option_values.select_related("option").order_by(
            "option__sort_order",
            "option__id",
            "sort_order",
            "id",
        )
        return ", ".join(f"{value.option.name}: {value.value}" for value in values)


def validate_variant_option_values(product, values):
    errors = {}
    option_ids = set()
    for value in values:
        if value.option.product_id != product.id:
            errors.setdefault("option_values", []).append(
                "All option values must belong to the same product as the variant."
            )
            continue
        if value.option_id in option_ids:
            errors.setdefault("option_values", []).append(
                "A variant cannot contain two values from the same option."
            )
        option_ids.add(value.option_id)
    return errors


class HomepageProductSlot(models.Model):
    class Section(models.TextChoices):
        HERO_SLIDER = "hero_slider", "Hero slider"
        POPULAR_MARQUEE = "popular_marquee", "Popular marquee"
        LATEST_CAROUSEL = "latest_carousel", "Latest carousel"
        FEATURED_PRODUCTS = "featured_products", "Featured products"

    section = models.CharField(max_length=30, choices=Section.choices)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="homepage_slots",
    )
    title_override = models.CharField(max_length=255, blank=True)
    subtitle_override = models.TextField(blank=True)
    badge_text = models.CharField(max_length=100, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("section", "sort_order", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("section", "product"),
                condition=Q(is_active=True),
                name="unique_active_homepage_product_per_section",
            )
        ]

    def __str__(self):
        return f"{self.get_section_display()} - {self.product}"


class WishlistItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlist_items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="wishlist_items",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("user", "product"),
                name="unique_wishlist_product_per_user",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.product}"


class ProductReview(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="product_reviews",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    rating = models.PositiveSmallIntegerField(
        validators=(MinValueValidator(1), MaxValueValidator(5))
    )
    comment = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("user", "product"),
                name="unique_review_per_user_product",
            ),
            models.CheckConstraint(
                condition=Q(rating__gte=1, rating__lte=5),
                name="product_review_rating_between_1_and_5",
            ),
        ]

    def __str__(self):
        return f"{self.product} review by {self.user}"
