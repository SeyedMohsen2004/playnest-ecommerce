from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0006_simplify_selected_options"),
        ("products", "0006_productoptionvalue_stock"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="cartitem",
            name="unique_product_per_cart",
        ),
        migrations.AddField(
            model_name="cartitem",
            name="selected_option_value_ids",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="selected_option_value_ids_snapshot",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
