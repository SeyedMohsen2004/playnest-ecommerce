from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0005_remove_product_variants"),
    ]

    operations = [
        migrations.AddField(
            model_name="productoptionvalue",
            name="stock",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
