from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0007_remove_product_options"),
    ]

    operations = [
        migrations.AlterField(
            model_name="homepageproductslot",
            name="section",
            field=models.CharField(
                choices=[
                    ("hero_slider", "بنر اصلی"),
                    ("popular_marquee", "محصولات پرطرفدار نواری"),
                    ("latest_carousel", "تازه‌های فروشگاه"),
                    ("featured_products", "محصولات منتخب"),
                ],
                max_length=30,
            ),
        ),
    ]
