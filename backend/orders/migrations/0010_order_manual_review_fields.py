from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0009_alter_order_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="requires_manual_review",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="order",
            name="manual_review_reason",
            field=models.TextField(blank=True, default=""),
        ),
    ]
