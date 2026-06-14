from rest_framework.routers import DefaultRouter

from products.views import BrandViewSet, CategoryViewSet, ProductViewSet

app_name = "products"

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("brands", BrandViewSet, basename="brand")
router.register("products", ProductViewSet, basename="product")

urlpatterns = router.urls
