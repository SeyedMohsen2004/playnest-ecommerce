from django.urls import path
from rest_framework.routers import DefaultRouter

from orders.views import (
    ApplyCouponView,
    CartItemCreateView,
    CartItemDetailView,
    CartView,
    CheckoutView,
    OrderViewSet,
)

app_name = "orders"

router = DefaultRouter()
router.register("orders", OrderViewSet, basename="order")

urlpatterns = [
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/apply-coupon/", ApplyCouponView.as_view(), name="apply-coupon"),
    path("cart/items/", CartItemCreateView.as_view(), name="cart-item-list"),
    path(
        "cart/items/<int:pk>/",
        CartItemDetailView.as_view(),
        name="cart-item-detail",
    ),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
] + router.urls
