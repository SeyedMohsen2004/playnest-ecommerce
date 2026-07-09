from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0004_product_options_variants"),
        ("orders", "0005_cartitem_variant_orderitem_variant"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="cartitem",
            name="unique_product_variant_per_cart",
        ),
        migrations.RemoveConstraint(
            model_name="cartitem",
            name="unique_simple_product_per_cart",
        ),
        migrations.RemoveField(
            model_name="cartitem",
            name="variant",
        ),
        migrations.RemoveField(
            model_name="orderitem",
            name="variant",
        ),
        migrations.AddField(
            model_name="cartitem",
            name="selected_options",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name="orderitem",
            name="selected_options_snapshot",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddConstraint(
            model_name="cartitem",
            constraint=models.UniqueConstraint(
                fields=("cart", "product"),
                name="unique_product_per_cart",
            ),
        ),
    ]
