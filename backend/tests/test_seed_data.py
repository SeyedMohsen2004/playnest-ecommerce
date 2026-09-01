import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from accounts.models import User
from orders.models import Coupon
from products.models import Brand, Category, Product, ProductImage

pytestmark = pytest.mark.django_db


def test_seed_data_command_runs_successfully_and_is_idempotent(settings, tmp_path):
    settings.DEBUG = True
    settings.MEDIA_ROOT = tmp_path

    call_command("seed_data")
    call_command("seed_data")

    admin = User.objects.get(phone_number="09120000000")
    customer = User.objects.get(phone_number="09121111111")
    assert admin.is_staff is True
    assert admin.is_superuser is True
    assert admin.check_password("AdminPass123!")
    assert customer.check_password("CustomerPass123!")
    assert Category.objects.count() == 7
    assert Brand.objects.count() == 5
    assert Product.objects.count() == 20
    assert ProductImage.objects.count() == 20
    assert set(Coupon.objects.values_list("code", flat=True)) == {
        "DEMO-OFF10",
        "DEMO-GAME50000",
    }


def test_seed_data_refuses_production_before_database_mutation(settings, tmp_path):
    settings.DEBUG = False
    settings.MEDIA_ROOT = tmp_path

    with pytest.raises(CommandError, match="development-only"):
        call_command("seed_data")

    assert User.objects.count() == 0
    assert Category.objects.count() == 0
    assert Brand.objects.count() == 0
    assert Product.objects.count() == 0
    assert ProductImage.objects.count() == 0
    assert Coupon.objects.count() == 0
