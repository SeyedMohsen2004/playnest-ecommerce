from django.contrib import admin

from products.models import (
    Brand,
    Category,
    Product,
    ProductImage,
    ProductReview,
    WishlistItem,
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "alt_text", "is_main", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "is_active", "created_at", "updated_at")
    search_fields = ("name", "description")
    list_filter = ("is_active", "created_at", "updated_at")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    ordering = ("name",)
    fieldsets = (
        (None, {"fields": ("name", "slug", "parent", "description")}),
        ("Status", {"fields": ("is_active",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at", "updated_at")
    search_fields = ("name", "description")
    list_filter = ("is_active", "created_at", "updated_at")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    ordering = ("name",)
    fieldsets = (
        (None, {"fields": ("name", "slug", "description")}),
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
        "stock",
        "is_active",
        "is_featured",
        "created_at",
    )
    search_fields = ("name", "description", "sku")
    list_filter = (
        "category",
        "brand",
        "age_group",
        "gender",
        "is_active",
        "is_featured",
    )
    list_select_related = ("category", "brand")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    inlines = (ProductImageInline,)
    fieldsets = (
        (
            "Product information",
            {
                "fields": (
                    "name",
                    "slug",
                    "sku",
                    "category",
                    "brand",
                    "description",
                    "short_description",
                )
            },
        ),
        ("Pricing and inventory", {"fields": ("price", "discount_price", "stock")}),
        ("Audience", {"fields": ("age_group", "gender")}),
        ("Visibility", {"fields": ("is_active", "is_featured")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
    ordering = ("-created_at",)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "alt_text", "is_main", "created_at")
    search_fields = ("product__name", "product__sku", "alt_text")
    list_filter = ("is_main", "created_at")
    list_select_related = ("product",)
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


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

    @admin.action(description="Approve selected reviews")
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description="Reject selected reviews")
    def reject_reviews(self, request, queryset):
        queryset.update(is_approved=False)
