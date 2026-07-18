from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0008_update_homepage_section_labels"),
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
                    ("board_games", "برد گیم‌ها"),
                    ("construction", "ساختنی‌ها"),
                    ("featured_products", "محصولات منتخب"),
                    ("educational", "آموزشی"),
                ],
                max_length=30,
            ),
        ),
    ]
