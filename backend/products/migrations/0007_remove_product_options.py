from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0006_productoptionvalue_stock"),
    ]

    operations = [
        migrations.DeleteModel(
            name="ProductOptionValue",
        ),
        migrations.DeleteModel(
            name="ProductOption",
        ),
    ]
