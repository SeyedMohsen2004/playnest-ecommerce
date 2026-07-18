from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="status_from_gateway",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
        migrations.AddField(
            model_name="payment",
            name="gateway_code",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="payment",
            name="gateway_message",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="payment",
            name="card_hash",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
        migrations.AddField(
            model_name="payment",
            name="fee",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="payment",
            name="fee_type",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
        migrations.AddField(
            model_name="payment",
            name="cart_finalized",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="payment",
            name="verified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
