from django.contrib import admin

from products.models import Brand, Category, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "alt_text", "is_main")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "is_active", "created_at", "updated_at")
    search_fields = ("name", "description")
    list_filter = ("is_active", "created_at", "updated_at")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at", "updated_at")
    search_fields = ("name", "description")
    list_filter = ("is_active", "created_at", "updated_at")
    prepopulated_fields = {"slug": ("name",)}


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
    inlines = (ProductImageInline,)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "alt_text", "is_main", "created_at")
    search_fields = ("product__name", "product__sku", "alt_text")
    list_filter = ("is_main", "created_at")
    list_select_related = ("product",)
