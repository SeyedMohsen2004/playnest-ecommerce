from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0002_productreview_wishlistitem"),
    ]

    operations = [
        migrations.CreateModel(
            name="HomepageProductSlot",
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
                (
                    "section",
                    models.CharField(
                        choices=[
                            ("hero_slider", "Hero slider"),
                            ("popular_marquee", "Popular marquee"),
                            ("latest_carousel", "Latest carousel"),
                            ("featured_products", "Featured products"),
                        ],
                        max_length=30,
                    ),
                ),
                ("title_override", models.CharField(blank=True, max_length=255)),
                ("subtitle_override", models.TextField(blank=True)),
                ("badge_text", models.CharField(blank=True, max_length=100)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="homepage_slots",
                        to="products.product",
                    ),
                ),
            ],
            options={
                "ordering": ("section", "sort_order", "id"),
            },
        ),
        migrations.AddConstraint(
            model_name="homepageproductslot",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_active", True)),
                fields=("section", "product"),
                name="unique_active_homepage_product_per_section",
            ),
        ),
    ]
