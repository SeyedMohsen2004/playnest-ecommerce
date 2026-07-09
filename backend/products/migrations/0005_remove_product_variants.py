from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0004_product_options_variants"),
        ("orders", "0006_simplify_selected_options"),
    ]

    operations = [
        migrations.DeleteModel(
            name="ProductVariant",
        ),
    ]
