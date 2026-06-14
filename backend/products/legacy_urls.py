from rest_framework.routers import SimpleRouter

from products.views import BrandViewSet, CategoryViewSet, ProductViewSet

app_name = "products_legacy"

router = SimpleRouter()
router.register("products", ProductViewSet, basename="product")
router.register("categories", CategoryViewSet, basename="category")
router.register("brands", BrandViewSet, basename="brand")

urlpatterns = router.urls
