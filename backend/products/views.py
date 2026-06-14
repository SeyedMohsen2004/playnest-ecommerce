from django.db.models import Avg, Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, viewsets

from products.filters import ProductFilter
from products.models import (
    Brand,
    Category,
    Product,
    ProductImage,
    ProductReview,
    WishlistItem,
)
from products.permissions import IsAdminOrReadOnly
from products.serializers import (
    BrandSerializer,
    CategorySerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    ProductReviewSerializer,
    WishlistItemSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.select_related("parent").all()
    serializer_class = CategorySerializer
    permission_classes = (IsAdminOrReadOnly,)
    lookup_field = "slug"

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            return queryset.filter(is_active=True)
        return queryset


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = (IsAdminOrReadOnly,)
    lookup_field = "slug"

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            return queryset.filter(is_active=True)
        return queryset


class ProductViewSet(viewsets.ModelViewSet):
    queryset = (
        Product.objects.select_related("category", "brand")
        .prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects.order_by("-is_main", "created_at"),
            )
        )
        .annotate(
            average_rating=Avg(
                "reviews__rating",
                filter=Q(reviews__is_approved=True),
            ),
            review_count=Count(
                "reviews",
                filter=Q(reviews__is_approved=True),
                distinct=True,
            ),
        )
    )
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    filterset_class = ProductFilter
    search_fields = ("name", "description", "sku")
    ordering_fields = ("price", "created_at")
    ordering = ("-created_at",)
    lookup_field = "slug"

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            return queryset.filter(
                is_active=True,
                category__is_active=True,
            ).filter(Q(brand__isnull=True) | Q(brand__is_active=True))
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        return ProductDetailSerializer


class WishlistListCreateView(generics.ListCreateAPIView):
    queryset = WishlistItem.objects.none()
    serializer_class = WishlistItemSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset
        return (
            self.request.user.wishlist_items.select_related(
                "product",
                "product__category",
                "product__brand",
            )
            .prefetch_related("product__images")
            .all()
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WishlistDestroyView(generics.DestroyAPIView):
    queryset = WishlistItem.objects.none()
    serializer_class = WishlistItemSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset
        return self.request.user.wishlist_items.all()


class ProductReviewListCreateView(generics.ListCreateAPIView):
    queryset = ProductReview.objects.none()
    serializer_class = ProductReviewSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return (permissions.AllowAny(),)
        return (permissions.IsAuthenticated(),)

    def get_product(self):
        if not hasattr(self, "_product"):
            self._product = get_object_or_404(
                Product.objects.filter(is_active=True),
                slug=self.kwargs["slug"],
            )
        return self._product

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset
        return ProductReview.objects.filter(
            product=self.get_product(),
            is_approved=True,
        ).select_related("user", "product")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if not getattr(self, "swagger_fake_view", False):
            context["product"] = self.get_product()
        return context

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, product=self.get_product())
