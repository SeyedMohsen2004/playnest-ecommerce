from django.db.models import Prefetch
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Cart, CartItem, Order
from orders.serializers import (
    ApplyCouponSerializer,
    CartItemCreateSerializer,
    CartItemSerializer,
    CartItemUpdateSerializer,
    CartSerializer,
    CartSummarySerializer,
    CheckoutSerializer,
    OrderSerializer,
)
from payments.models import Payment
from products.models import ProductImage


def get_user_cart(user):
    return Cart.objects.prefetch_related(
        "items__product",
        Prefetch(
            "items__product__images",
            queryset=ProductImage.objects.order_by("-is_main", "created_at"),
        ),
    ).get_or_create(user=user)[0]


class CartView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(responses={200: CartSerializer})
    def get(self, request):
        return Response(
            CartSerializer(
                get_user_cart(request.user),
                context={"request": request},
            ).data
        )


class ApplyCouponView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=ApplyCouponSerializer,
        responses={200: CartSummarySerializer},
    )
    def post(self, request):
        cart = get_user_cart(request.user)
        serializer = ApplyCouponSerializer(
            data=request.data,
            context={"cart": cart},
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.save())


class CartItemCreateView(generics.CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CartItemCreateSerializer

    def perform_create(self, serializer):
        self.item = serializer.save(cart=get_user_cart(self.request.user))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        item = (
            CartItem.objects.select_related("product")
            .prefetch_related(
                Prefetch(
                    "product__images",
                    queryset=ProductImage.objects.order_by("-is_main", "created_at"),
                )
            )
            .get(pk=self.item.pk)
        )
        return Response(
            CartItemSerializer(item, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class CartItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CartItemUpdateSerializer
    http_method_names = ("patch", "delete", "head", "options")

    def get_queryset(self):
        return (
            CartItem.objects.select_related("product")
            .filter(cart__user=self.request.user)
        )


class CheckoutView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=CheckoutSerializer, responses={201: OrderSerializer})
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        order = Order.objects.prefetch_related("items").get(pk=order.pk)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Order.objects.none()
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = Order.objects.select_related("user").prefetch_related(
            "items__product__images",
            "payments",
        )
        if getattr(self, "swagger_fake_view", False):
            return queryset.none()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(user=self.request.user)

    @action(detail=True, methods=("post",), url_path="cancel")
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status == Order.Status.CANCELLED:
            return Response(
                {"detail": "این سفارش قبلاً لغو شده است."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if order.status not in (Order.Status.PENDING, Order.Status.PAYMENT_FAILED):
            return Response(
                {"detail": "امکان لغو این سفارش وجود ندارد."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        now = timezone.now()
        order.status = Order.Status.CANCELLED
        order.save(update_fields=("status", "updated_at"))
        order.payments.filter(status=Payment.Status.PENDING).update(
            status=Payment.Status.CANCELLED,
            updated_at=now,
        )
        order = self.get_queryset().get(pk=order.pk)
        return Response(self.get_serializer(order).data)
