from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("orders", "0012_couponredemption_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="coupon",
            name="per_user_usage_limit",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddConstraint(
            model_name="coupon",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("per_user_usage_limit__isnull", True),
                    ("per_user_usage_limit__gte", 1),
                    _connector="OR",
                ),
                name="coupon_per_user_usage_limit_positive",
            ),
        ),
        migrations.CreateModel(
            name="CouponValidationThrottle",
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
                ("attempt_count", models.PositiveIntegerField(default=0)),
                ("window_started_at", models.DateTimeField()),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="coupon_validation_throttle",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
