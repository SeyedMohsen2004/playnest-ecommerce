import math
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework.throttling import SimpleRateThrottle

from orders.models import CouponValidationThrottle


class CouponApplyThrottle(SimpleRateThrottle):
    """Database-backed per-user limit for coupon validation attempts."""

    scope = "coupon_apply"

    def get_cache_key(self, request, view):
        return None

    def allow_request(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return True

        window = timedelta(seconds=self.duration)
        with transaction.atomic():
            get_user_model().objects.select_for_update().only("pk").get(
                pk=request.user.pk
            )
            now = timezone.now()
            throttle, _created = CouponValidationThrottle.objects.get_or_create(
                user_id=request.user.pk,
                defaults={"window_started_at": now},
            )
            if now >= throttle.window_started_at + window:
                throttle.attempt_count = 0
                throttle.window_started_at = now

            if throttle.attempt_count >= self.num_requests:
                self.available_at = throttle.window_started_at + window
                return False

            throttle.attempt_count += 1
            throttle.save(
                update_fields=("attempt_count", "window_started_at", "updated_at")
            )
        return True

    def wait(self):
        remaining = (self.available_at - timezone.now()).total_seconds()
        return max(1, math.ceil(remaining))
