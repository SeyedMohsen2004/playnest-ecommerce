from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0004_product_options_variants"),
        ("orders", "0004_coupon_coupon_percentage_maximum_100"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="cartitem",
            name="unique_product_per_cart",
        ),
        migrations.AddField(
            model_name="cartitem",
            name="variant",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="cart_items",
                to="products.productvariant",
            ),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="selected_options_snapshot",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="variant",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="order_items",
                to="products.productvariant",
            ),
        ),
        migrations.AddConstraint(
            model_name="cartitem",
            constraint=models.UniqueConstraint(
                fields=("cart", "product", "variant"),
                name="unique_product_variant_per_cart",
            ),
        ),
        migrations.AddConstraint(
            model_name="cartitem",
            constraint=models.UniqueConstraint(
                condition=models.Q(variant__isnull=True),
                fields=("cart", "product"),
                name="unique_simple_product_per_cart",
            ),
        ),
    ]
