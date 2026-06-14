from drf_spectacular.utils import extend_schema
from rest_framework import generics, status, viewsets
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


def get_user_cart(user):
    return Cart.objects.prefetch_related("items__product").get_or_create(user=user)[0]


class CartView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(responses={200: CartSerializer})
    def get(self, request):
        return Response(CartSerializer(get_user_cart(request.user)).data)


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
        return Response(
            CartItemSerializer(self.item).data,
            status=status.HTTP_201_CREATED,
        )


class CartItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CartItemUpdateSerializer
    http_method_names = ("patch", "delete", "head", "options")

    def get_queryset(self):
        return CartItem.objects.select_related("product").filter(
            cart__user=self.request.user
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
        queryset = Order.objects.select_related("user").prefetch_related("items")
        if getattr(self, "swagger_fake_view", False):
            return queryset.none()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(user=self.request.user)
