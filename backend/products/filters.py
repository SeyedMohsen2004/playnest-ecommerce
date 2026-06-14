from django.db.models import Q
from django_filters import rest_framework as filters

from products.models import Product


class ProductFilter(filters.FilterSet):
    min_price = filters.NumberFilter(method="filter_min_price")
    max_price = filters.NumberFilter(method="filter_max_price")
    in_stock = filters.BooleanFilter(method="filter_in_stock")

    class Meta:
        model = Product
        fields = (
            "category",
            "brand",
            "age_group",
            "gender",
            "is_featured",
        )

    def filter_min_price(self, queryset, name, value):
        return queryset.filter(
            Q(discount_price__isnull=False, discount_price__gte=value)
            | Q(discount_price__isnull=True, price__gte=value)
        )

    def filter_max_price(self, queryset, name, value):
        return queryset.filter(
            Q(discount_price__isnull=False, discount_price__lte=value)
            | Q(discount_price__isnull=True, price__lte=value)
        )

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__gt=0)
        return queryset.filter(stock=0)
