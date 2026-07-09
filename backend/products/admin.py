from django import forms
from django.contrib import admin

from products.models import (
    Brand,
    Category,
    HomepageProductSlot,
    Product,
    ProductImage,
    ProductOption,
    ProductOptionValue,
    ProductReview,
    ProductVariant,
    WishlistItem,
    validate_variant_option_values,
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "alt_text", "is_main", "created_at")
    readonly_fields = ("created_at",)
    show_change_link = True


class ProductOptionInline(admin.TabularInline):
    model = ProductOption
    extra = 0
    fields = ("name", "sort_order", "is_active")
    show_change_link = True


class ProductVariantAdminForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get("product")
        option_values = list(cleaned_data.get("option_values") or [])
        if not product or not option_values:
            return cleaned_data

        errors = validate_variant_option_values(product, option_values)
        if errors:
            raise forms.ValidationError(errors)

        selected_value_ids = sorted(value.id for value in option_values)
        existing_variants = (
            ProductVariant.objects.filter(product=product)
            .exclude(pk=self.instance.pk)
            .prefetch_related("option_values")
        )
        for variant in existing_variants:
            variant_value_ids = sorted(
                variant.option_values.values_list("id", flat=True)
            )
            if variant_value_ids == selected_value_ids:
                raise forms.ValidationError(
                    {"option_values": "This variant combination already exists."}
                )

        return cleaned_data


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "is_active", "created_at")
    search_fields = ("name", "slug", "description")
    list_filter = ("is_active", "parent")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    ordering = ("name",)
    date_hierarchy = "created_at"
    fieldsets = (
        ("Basic information", {"fields": ("name", "parent", "description")}),
        ("SEO / slug", {"fields": ("slug",)}),
        ("Status", {"fields": ("is_active",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    search_fields = ("name", "slug", "description")
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    ordering = ("name",)
    date_hierarchy = "created_at"
    fieldsets = (
        ("Basic information", {"fields": ("name", "description")}),
        ("SEO / slug", {"fields": ("slug",)}),
        ("Status", {"fields": ("is_active",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "sku",
        "category",
        "brand",
        "price",
        "discount_price",
        "final_price_display",
        "stock",
        "is_in_stock_display",
        "is_active",
        "is_featured",
        "created_at",
    )
    search_fields = ("name", "slug", "sku", "short_description", "description")
    list_filter = (
        "category",
        "brand",
        "is_active",
        "is_featured",
        "age_group",
        "gender",
        "created_at",
    )
    list_select_related = ("category", "brand")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = (
        "final_price_display",
        "is_in_stock_display",
        "created_at",
        "updated_at",
    )
    list_editable = ("price", "stock", "is_active", "is_featured")
    autocomplete_fields = ("category", "brand")
    inlines = (ProductImageInline, ProductOptionInline)
    date_hierarchy = "created_at"
    fieldsets = (
        (
            "Basic information",
            {
                "fields": (
                    "name",
                    "sku",
                    "short_description",
                    "description",
                )
            },
        ),
        (
            "Pricing",
            {"fields": ("price", "discount_price", "final_price_display")},
        ),
        ("Inventory", {"fields": ("stock", "is_in_stock_display")}),
        ("Classification", {"fields": ("category", "brand", "age_group", "gender")}),
        ("Display options", {"fields": ("is_active", "is_featured")}),
        ("SEO / slug", {"fields": ("slug",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
    ordering = ("-created_at",)

    @admin.display(description="Final price", ordering="discount_price")
    def final_price_display(self, obj):
        return obj.final_price

    @admin.display(boolean=True, description="In stock")
    def is_in_stock_display(self, obj):
        return obj.is_in_stock


@admin.register(ProductOption)
class ProductOptionAdmin(admin.ModelAdmin):
    list_display = ("product", "name", "sort_order", "is_active")
    list_filter = ("product", "is_active")
    search_fields = ("product__name", "product__sku", "name")
    list_select_related = ("product",)
    autocomplete_fields = ("product",)
    list_editable = ("sort_order", "is_active")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("product__name", "sort_order", "id")


@admin.register(ProductOptionValue)
class ProductOptionValueAdmin(admin.ModelAdmin):
    list_display = ("option", "value", "sort_order", "is_active")
    list_filter = ("option", "is_active")
    search_fields = ("option__name", "value", "option__product__name")
    list_select_related = ("option", "option__product")
    autocomplete_fields = ("option",)
    list_editable = ("sort_order", "is_active")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("option__product__name", "option__sort_order", "sort_order", "id")


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    form = ProductVariantAdminForm
    list_display = (
        "product",
        "display_option_values",
        "sku",
        "price",
        "stock",
        "is_active",
        "sort_order",
    )
    list_filter = ("product", "is_active")
    search_fields = (
        "product__name",
        "product__sku",
        "sku",
        "option_values__value",
    )
    list_select_related = ("product",)
    autocomplete_fields = ("product",)
    filter_horizontal = ("option_values",)
    list_editable = ("price", "stock", "is_active", "sort_order")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("product__name", "sort_order", "id")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("product")
            .prefetch_related("option_values__option")
        )

    @admin.display(description="Options")
    def display_option_values(self, obj):
        return obj.selected_options_label


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "alt_text", "is_main", "created_at")
    search_fields = ("product__name", "product__sku", "alt_text")
    list_filter = ("is_main", "created_at")
    list_select_related = ("product",)
    readonly_fields = ("created_at",)
    autocomplete_fields = ("product",)
    ordering = ("-created_at",)


@admin.register(HomepageProductSlot)
class HomepageProductSlotAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "section",
        "sort_order",
        "is_active",
        "badge_text",
        "updated_at",
    )
    search_fields = ("product__name", "product__sku", "title_override")
    list_filter = ("section", "is_active")
    list_select_related = ("product", "product__category", "product__brand")
    autocomplete_fields = ("product",)
    readonly_fields = ("created_at", "updated_at")
    list_editable = ("sort_order", "is_active")
    ordering = ("section", "sort_order", "id")
    fieldsets = (
        (
            "Homepage section",
            {
                "fields": ("section", "product", "sort_order", "is_active"),
                "description": (
                    "Hero slider: top banner products. Popular marquee: "
                    "continuous moving strip. Latest carousel: one-card step "
                    "slider. Featured products: selected products block."
                ),
            },
        ),
        (
            "Optional display overrides",
            {"fields": ("title_override", "subtitle_override", "badge_text")},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "created_at")
    search_fields = ("user__phone_number", "product__name", "product__sku")
    list_filter = ("created_at",)
    list_select_related = ("user", "product")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "is_approved", "created_at")
    search_fields = (
        "product__name",
        "user__phone_number",
        "comment",
    )
    list_filter = ("rating", "is_approved", "created_at")
    list_select_related = ("user", "product")
    list_editable = ("is_approved",)
    readonly_fields = ("created_at", "updated_at")
    actions = ("approve_reviews", "reject_reviews")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    fieldsets = (
        ("Review", {"fields": ("product", "user", "rating", "comment")}),
        ("Moderation", {"fields": ("is_approved",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    @admin.action(description="تایید دیدگاه‌های انتخاب‌شده")
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description="رد دیدگاه‌های انتخاب‌شده")
    def reject_reviews(self, request, queryset):
        queryset.update(is_approved=False)
