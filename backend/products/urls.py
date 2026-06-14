from django.urls import path
from rest_framework.routers import DefaultRouter

from products.views import (
    BrandViewSet,
    CategoryViewSet,
    ProductReviewListCreateView,
    ProductViewSet,
    WishlistDestroyView,
    WishlistListCreateView,
)

app_name = "products"

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
router.register("categories", CategoryViewSet, basename="category")
router.register("brands", BrandViewSet, basename="brand")

urlpatterns = [
    path(
        "wishlist/",
        WishlistListCreateView.as_view(),
        name="wishlist-list",
    ),
    path(
        "wishlist/<int:pk>/",
        WishlistDestroyView.as_view(),
        name="wishlist-detail",
    ),
    path(
        "products/<slug:slug>/reviews/",
        ProductReviewListCreateView.as_view(),
        name="product-reviews",
    ),
] + router.urls
