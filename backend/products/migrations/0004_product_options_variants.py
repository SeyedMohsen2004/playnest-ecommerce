from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0003_homepageproductslot"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductOption",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="options",
                        to="products.product",
                    ),
                ),
            ],
            options={
                "ordering": ("sort_order", "id"),
            },
        ),
        migrations.CreateModel(
            name="ProductOptionValue",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("value", models.CharField(max_length=100)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "option",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="values",
                        to="products.productoption",
                    ),
                ),
            ],
            options={
                "ordering": ("option__sort_order", "sort_order", "id"),
            },
        ),
        migrations.CreateModel(
            name="ProductVariant",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("sku", models.CharField(blank=True, max_length=100)),
                ("price", models.PositiveIntegerField()),
                ("stock", models.PositiveIntegerField(default=0)),
                (
                    "image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="products/variants/",
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "option_values",
                    models.ManyToManyField(
                        related_name="variants",
                        to="products.productoptionvalue",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="variants",
                        to="products.product",
                    ),
                ),
            ],
            options={
                "ordering": ("sort_order", "id"),
            },
        ),
        migrations.AddConstraint(
            model_name="productoption",
            constraint=models.UniqueConstraint(
                fields=("product", "name"),
                name="unique_product_option_name",
            ),
        ),
        migrations.AddConstraint(
            model_name="productoptionvalue",
            constraint=models.UniqueConstraint(
                fields=("option", "value"),
                name="unique_product_option_value",
            ),
        ),
        migrations.AddConstraint(
            model_name="productvariant",
            constraint=models.UniqueConstraint(
                condition=~models.Q(sku=""),
                fields=("sku",),
                name="unique_non_blank_product_variant_sku",
            ),
        ),
    ]
