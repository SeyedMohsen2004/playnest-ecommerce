from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, close_old_connections, connections, transaction

from accounts.models import User
from orders.models import (
    Cart,
    CartItem,
    Coupon,
    CouponRedemption,
    Order,
    OrderItem,
    ShippingSettings,
)
from orders.services import (
    CouponCapacityUnavailable,
    OrderCancellationNotAllowed,
    ShippingUpdateNotAllowed,
    cancel_order,
    checkout_cart,
    update_order_shipping,
)
from payments.models import Payment
from payments.services import (
    COUPON_REDEMPTION_REVIEW_REASON,
    INVENTORY_REVIEW_REASON,
    LOCAL_CONSTRAINT_REVIEW_REASON,
    VERIFICATION_CONFLICT_REVIEW_REASON,
    finalize_verified_payment,
    prepare_payment_attempt,
    record_failed_callback,
    record_verification_uncertainty,
)
from payments.services.zarinpal import PaymentVerificationResult
from products.models import Brand, Category, Product

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def category():
    return Category.objects.create(name="Concurrent Toys", slug="concurrent-toys")


@pytest.fixture
def brand():
    return Brand.objects.create(name="Concurrent Brand", slug="concurrent-brand")


@pytest.fixture
def product(category, brand):
    return Product.objects.create(
        category=category,
        brand=brand,
        name="Concurrent Toy",
        slug="concurrent-toy",
        description="Concurrency test product.",
        sku="CONCURRENT-001",
        price=1000,
        stock=10,
        age_group=Product.AgeGroup.THREE_TO_FIVE,
        gender=Product.Gender.UNISEX,
    )


def create_user(index):
    return User.objects.create_user(
        phone_number=f"0912000{index:04d}",
        password="StrongPassword!42",
        is_active=True,
        is_phone_verified=True,
    )


def create_order(user, product, *, quantity=1, coupon=None, cart_item=None):
    order = Order.objects.create(
        user=user,
        coupon=coupon,
        subtotal_amount=product.final_price * quantity,
        total_amount=product.final_price * quantity,
        shipping_address="Concurrent address",
        postal_code="1234567890",
        recipient_name="Concurrent User",
        recipient_phone=user.phone_number,
    )
    OrderItem.objects.create(
        order=order,
        product=product,
        product_name=product.name,
        product_price=product.final_price,
        quantity=quantity,
        line_total=product.final_price * quantity,
        cart_item_id_snapshot=cart_item.pk if cart_item else None,
    )
    return order


def create_payment(user, order, authority):
    return Payment.objects.create(
        user=user,
        order=order,
        amount=order.total_amount,
        authority=authority,
    )


def verification(ref_id):
    return PaymentVerificationResult(
        code=100,
        message="Verified",
        ref_id=ref_id,
        card_pan="603799******1234",
        card_hash=f"hash-{ref_id}",
        fee=0,
        fee_type="Merchant",
        gateway_response={"data": {"code": 100, "ref_id": ref_id}},
    )


def checkout_for(user, *, coupon_code=""):
    return checkout_cart(
        user=user,
        shipping_address="Concurrent address",
        postal_code="1234567890",
        recipient_name="Concurrent User",
        recipient_phone=user.phone_number,
        shipping_zone=Order.ShippingZone.TABRIZ,
        coupon_code=coupon_code,
    )


def run_concurrently(*operations):
    barrier = Barrier(len(operations), timeout=10)

    def run(operation):
        close_old_connections()
        try:
            barrier.wait()
            return operation()
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=len(operations)) as executor:
        futures = [executor.submit(run, operation) for operation in operations]
        return [future.result(timeout=20) for future in futures]


def test_two_concurrent_cancellations_are_service_idempotent(product):
    user = create_user(1)
    order = create_order(user, product)
    payment = create_payment(user, order, "A" * 36)

    results = run_concurrently(
        lambda: cancel_order(order.id),
        lambda: cancel_order(order.id),
    )

    order.refresh_from_db()
    payment.refresh_from_db()
    assert order.status == Order.Status.CANCELLED
    assert payment.status == Payment.Status.CANCELLED
    assert sum(result.cancelled for result in results) == 1
    assert sum(result.already_cancelled for result in results) == 1


def test_cancellation_racing_verified_payment_has_one_safe_outcome(product):
    user = create_user(2)
    order = create_order(user, product, quantity=2)
    payment = create_payment(user, order, "B" * 36)

    def cancel():
        try:
            return "cancelled" if cancel_order(order.id).cancelled else "repeat"
        except OrderCancellationNotAllowed:
            return "rejected"

    def finalize():
        return finalize_verified_payment(
            payment.id,
            authority=payment.authority,
            verification=verification("cancel-race"),
        )

    cancel_result, finalization = run_concurrently(cancel, finalize)

    order.refresh_from_db()
    payment.refresh_from_db()
    product.refresh_from_db()
    assert payment.status == Payment.Status.PAID
    if cancel_result == "cancelled":
        assert order.status == Order.Status.CANCELLED
        assert order.requires_manual_review is True
        assert order.stock_reduced is False
        assert product.stock == 10
        assert finalization.order_paid is False
    else:
        assert cancel_result == "rejected"
        assert order.status == Order.Status.PAID
        assert order.stock_reduced is True
        assert product.stock == 8
        assert finalization.order_paid is True


def test_duplicate_concurrent_finalization_reduces_stock_and_cart_once(product):
    user = create_user(3)
    cart = Cart.objects.create(user=user)
    cart_item = CartItem.objects.create(cart=cart, product=product, quantity=4)
    order = create_order(user, product, quantity=2, cart_item=cart_item)
    payment = create_payment(user, order, "C" * 36)

    run_concurrently(
        lambda: finalize_verified_payment(
            payment.id,
            authority=payment.authority,
            verification=verification("duplicate"),
        ),
        lambda: finalize_verified_payment(
            payment.id,
            authority=payment.authority,
            verification=verification("duplicate"),
        ),
    )

    order.refresh_from_db()
    payment.refresh_from_db()
    product.refresh_from_db()
    cart_item.refresh_from_db()
    assert order.stock_reduced is True
    assert payment.cart_finalized is True
    assert product.stock == 8
    assert cart_item.quantity == 2


def test_failed_callback_racing_success_never_downgrades_paid_state(product):
    user = create_user(4)
    order = create_order(user, product)
    payment = create_payment(user, order, "D" * 36)

    run_concurrently(
        lambda: finalize_verified_payment(
            payment.id,
            authority=payment.authority,
            verification=verification("failure-race"),
        ),
        lambda: record_failed_callback(
            payment.id,
            callback_status="NOK",
            gateway_code=-51,
            gateway_message="Rejected",
        ),
    )

    payment.refresh_from_db()
    order.refresh_from_db()
    product.refresh_from_db()
    assert payment.status == Payment.Status.PAID
    assert payment.ref_id == "failure-race"
    assert order.status == Order.Status.PAID
    assert order.stock_reduced is True
    assert product.stock == 9


def test_conflicting_duplicate_verification_keeps_original_paid_evidence(product):
    user = create_user(17)
    order = create_order(user, product)
    payment = create_payment(user, order, "L" * 36)

    finalize_verified_payment(
        payment.id,
        authority=payment.authority,
        verification=verification("original-reference"),
    )
    result = finalize_verified_payment(
        payment.id,
        authority=payment.authority,
        verification=verification("conflicting-reference"),
    )
    benign_result = finalize_verified_payment(
        payment.id,
        authority=payment.authority,
        verification=verification("original-reference"),
    )

    payment.refresh_from_db()
    order.refresh_from_db()
    product.refresh_from_db()
    assert payment.status == Payment.Status.PAID
    assert payment.ref_id == "original-reference"
    assert payment.card_hash == "hash-original-reference"
    assert payment.gateway_response == {
        "data": {"code": 100, "ref_id": "original-reference"}
    }
    assert order.requires_manual_review is True
    assert order.manual_review_reason == VERIFICATION_CONFLICT_REVIEW_REASON
    assert result.requires_manual_review is True
    assert benign_result.requires_manual_review is True
    assert product.stock == 9


def test_stronger_manual_review_reason_survives_weaker_inventory_failure(product):
    user = create_user(20)
    order = create_order(user, product)
    order.requires_manual_review = True
    order.manual_review_reason = VERIFICATION_CONFLICT_REVIEW_REASON
    order.save(update_fields=("requires_manual_review", "manual_review_reason"))
    product.stock = 0
    product.save(update_fields=("stock",))
    payment = create_payment(user, order, "O" * 36)

    result = finalize_verified_payment(
        payment.id,
        authority=payment.authority,
        verification=verification("review-priority"),
    )

    payment.refresh_from_db()
    order.refresh_from_db()
    assert payment.status == Payment.Status.PAID
    assert order.requires_manual_review is True
    assert order.manual_review_reason == VERIFICATION_CONFLICT_REVIEW_REASON
    assert result.requires_manual_review is True


def test_recoverable_inventory_review_clears_only_after_side_effects_complete(product):
    user = create_user(21)
    order = create_order(user, product)
    product.stock = 0
    product.save(update_fields=("stock",))
    payment = create_payment(user, order, "P" * 36)

    first_result = finalize_verified_payment(
        payment.id,
        authority=payment.authority,
        verification=verification("inventory-recovery"),
    )
    order.refresh_from_db()
    assert first_result.requires_manual_review is True
    assert order.manual_review_reason == INVENTORY_REVIEW_REASON
    assert order.stock_reduced is False

    product.stock = 1
    product.save(update_fields=("stock",))
    second_result = finalize_verified_payment(
        payment.id,
        authority=payment.authority,
        verification=verification("inventory-recovery"),
    )

    payment.refresh_from_db()
    order.refresh_from_db()
    product.refresh_from_db()
    assert payment.status == Payment.Status.PAID
    assert payment.cart_finalized is True
    assert order.stock_reduced is True
    assert order.requires_manual_review is False
    assert order.manual_review_reason == ""
    assert second_result.requires_manual_review is False
    assert product.stock == 0


def test_verification_uncertainty_after_paid_does_not_overwrite_evidence(product):
    user = create_user(18)
    order = create_order(user, product)
    payment = create_payment(user, order, "M" * 36)
    finalize_verified_payment(
        payment.id,
        authority=payment.authority,
        verification=verification("certain-reference"),
    )

    record_verification_uncertainty(
        payment.id,
        gateway_message="Inferior transport result",
        gateway_response={"error": "transport"},
    )

    payment.refresh_from_db()
    assert payment.status == Payment.Status.PAID
    assert payment.ref_id == "certain-reference"
    assert payment.gateway_message == "Verified"
    assert payment.gateway_response == {
        "data": {"code": 100, "ref_id": "certain-reference"}
    }


def test_concurrent_checkouts_cannot_overreserve_final_coupon_capacity(product):
    ShippingSettings.load()
    coupon = Coupon.objects.create(
        code="FINAL-SLOT",
        discount_type=Coupon.DiscountType.FIXED,
        discount_value=100,
        usage_limit=1,
    )
    users = [create_user(5), create_user(6)]
    for user in users:
        CartItem.objects.create(
            cart=Cart.objects.create(user=user),
            product=product,
            quantity=1,
        )

    def attempt(user):
        try:
            return checkout_for(user, coupon_code=coupon.code).id
        except CouponCapacityUnavailable:
            return None

    order_ids = run_concurrently(*(lambda user=user: attempt(user) for user in users))

    assert sum(order_id is not None for order_id in order_ids) == 1
    assert (
        CouponRedemption.objects.filter(
            coupon=coupon,
            state=CouponRedemption.State.RESERVED,
        ).count()
        == 1
    )
    coupon.refresh_from_db()
    assert coupon.used_count == 0

    order = Order.objects.get(pk=next(order_id for order_id in order_ids if order_id))
    payment = create_payment(order.user, order, "E" * 36)
    finalize_verified_payment(
        payment.id,
        authority=payment.authority,
        verification=verification("coupon-final"),
    )
    coupon.refresh_from_db()
    assert coupon.used_count == coupon.usage_limit == 1
    assert order.coupon_redemption.state == CouponRedemption.State.CONSUMED


def test_retry_reuses_one_coupon_reservation_and_consumes_once(product):
    ShippingSettings.load()
    user = create_user(7)
    coupon = Coupon.objects.create(
        code="RETRY-ONCE",
        discount_type=Coupon.DiscountType.FIXED,
        discount_value=100,
        usage_limit=1,
    )
    CartItem.objects.create(
        cart=Cart.objects.create(user=user),
        product=product,
        quantity=1,
    )
    order = checkout_for(user, coupon_code=coupon.code)
    first_payment = prepare_payment_attempt(order.id)
    record_failed_callback(first_payment.id, callback_status="NOK")

    second_payment = prepare_payment_attempt(order.id)
    second_payment.authority = "F" * 36
    second_payment.save(update_fields=("authority",))
    finalize_verified_payment(
        second_payment.id,
        authority=second_payment.authority,
        verification=verification("retry"),
    )

    coupon.refresh_from_db()
    assert first_payment.id != second_payment.id
    assert CouponRedemption.objects.filter(order=order).count() == 1
    assert coupon.used_count == 1
    assert coupon.used_count <= coupon.usage_limit


def test_late_success_from_older_attempt_does_not_repeat_order_side_effects(product):
    ShippingSettings.load()
    user = create_user(14)
    coupon = Coupon.objects.create(
        code="LATE-RETRY",
        discount_type=Coupon.DiscountType.FIXED,
        discount_value=100,
        usage_limit=1,
    )
    cart_item = CartItem.objects.create(
        cart=Cart.objects.create(user=user),
        product=product,
        quantity=1,
    )
    order = checkout_for(user, coupon_code=coupon.code)
    cart_item.quantity = 3
    cart_item.save(update_fields=("quantity",))
    first_payment = create_payment(user, order, "J" * 36)
    record_failed_callback(first_payment.id, callback_status="NOK")
    second_payment = create_payment(user, order, "K" * 36)

    finalize_verified_payment(
        second_payment.id,
        authority=second_payment.authority,
        verification=verification("newer-attempt"),
    )
    late_result = finalize_verified_payment(
        first_payment.id,
        authority=first_payment.authority,
        verification=verification("older-attempt"),
    )

    order.refresh_from_db()
    first_payment.refresh_from_db()
    second_payment.refresh_from_db()
    product.refresh_from_db()
    coupon.refresh_from_db()
    cart_item.refresh_from_db()
    assert first_payment.status == Payment.Status.PAID
    assert second_payment.status == Payment.Status.PAID
    assert order.stock_reduced is True
    assert order.requires_manual_review is True
    assert late_result.requires_manual_review is True
    assert product.stock == 9
    assert coupon.used_count == 1
    assert order.coupon_redemption.state == CouponRedemption.State.CONSUMED
    assert cart_item.quantity == 2


def test_cancellation_releases_coupon_capacity_for_another_checkout(product):
    ShippingSettings.load()
    coupon = Coupon.objects.create(
        code="RELEASE-SLOT",
        discount_type=Coupon.DiscountType.FIXED,
        discount_value=100,
        usage_limit=1,
    )
    first_user = create_user(15)
    second_user = create_user(16)
    for user in (first_user, second_user):
        CartItem.objects.create(
            cart=Cart.objects.create(user=user),
            product=product,
            quantity=1,
        )

    first_order = checkout_for(first_user, coupon_code=coupon.code)
    first_payment = prepare_payment_attempt(first_order.id)
    cancel_order(first_order.id)
    second_order = checkout_for(second_user, coupon_code=coupon.code)

    first_payment.refresh_from_db()
    assert first_payment.status == Payment.Status.CANCELLED
    assert (
        CouponRedemption.objects.get(order=first_order).state
        == CouponRedemption.State.RELEASED
    )
    assert (
        CouponRedemption.objects.get(order=second_order).state
        == CouponRedemption.State.RESERVED
    )
    assert coupon.redemptions.filter(state=CouponRedemption.State.RESERVED).count() == 1


def test_verified_legacy_coupon_conflict_preserves_payment_for_manual_review(product):
    user = create_user(19)
    coupon = Coupon.objects.create(
        code="LEGACY-FULL",
        discount_type=Coupon.DiscountType.FIXED,
        discount_value=100,
        usage_limit=1,
        used_count=1,
    )
    order = create_order(user, product, coupon=coupon)
    payment = create_payment(user, order, "N" * 36)

    result = finalize_verified_payment(
        payment.id,
        authority=payment.authority,
        verification=verification("legacy-capacity"),
    )

    payment.refresh_from_db()
    order.refresh_from_db()
    coupon.refresh_from_db()
    product.refresh_from_db()
    assert payment.status == Payment.Status.PAID
    assert payment.ref_id == "legacy-capacity"
    assert order.status == Order.Status.PAID
    assert order.requires_manual_review is True
    assert order.stock_reduced is False
    assert result.requires_manual_review is True
    assert coupon.used_count == coupon.usage_limit == 1
    assert CouponRedemption.objects.filter(order=order).exists() is False
    assert product.stock == 10


def test_coupon_redemption_inconsistency_has_its_own_review_category(product):
    user = create_user(22)
    order_coupon = Coupon.objects.create(
        code="ORDER-COUPON",
        discount_type=Coupon.DiscountType.FIXED,
        discount_value=100,
    )
    wrong_coupon = Coupon.objects.create(
        code="WRONG-COUPON",
        discount_type=Coupon.DiscountType.FIXED,
        discount_value=100,
    )
    order = create_order(user, product, coupon=order_coupon)
    CouponRedemption.objects.create(coupon=wrong_coupon, order=order)
    payment = create_payment(user, order, "Q" * 36)

    result = finalize_verified_payment(
        payment.id,
        authority=payment.authority,
        verification=verification("coupon-inconsistency"),
    )

    payment.refresh_from_db()
    order.refresh_from_db()
    product.refresh_from_db()
    assert payment.status == Payment.Status.PAID
    assert payment.ref_id == "coupon-inconsistency"
    assert order.requires_manual_review is True
    assert order.manual_review_reason == COUPON_REDEMPTION_REVIEW_REASON
    assert order.manual_review_reason != INVENTORY_REVIEW_REASON
    assert order.stock_reduced is False
    assert product.stock == 10
    assert result.requires_manual_review is True


def test_local_integrity_error_preserves_paid_evidence_and_rolls_back_side_effects(
    product,
):
    user = create_user(23)
    coupon = Coupon.objects.create(
        code="SAVEPOINT",
        discount_type=Coupon.DiscountType.FIXED,
        discount_value=100,
        usage_limit=1,
    )
    cart_item = CartItem.objects.create(
        cart=Cart.objects.create(user=user),
        product=product,
        quantity=2,
    )
    order = create_order(
        user,
        product,
        coupon=coupon,
        cart_item=cart_item,
    )
    redemption = CouponRedemption.objects.create(coupon=coupon, order=order)
    payment = create_payment(user, order, "R" * 36)

    from payments import services as payment_services

    original_finalize_cart = payment_services._finalize_cart

    def finalize_cart_then_fail(*args, **kwargs):
        original_finalize_cart(*args, **kwargs)
        raise IntegrityError("Synthetic local constraint failure")

    with patch(
        "payments.services._finalize_cart",
        side_effect=finalize_cart_then_fail,
    ):
        result = finalize_verified_payment(
            payment.id,
            authority=payment.authority,
            verification=verification("savepoint-evidence"),
        )

    payment.refresh_from_db()
    order.refresh_from_db()
    product.refresh_from_db()
    coupon.refresh_from_db()
    redemption.refresh_from_db()
    cart_item.refresh_from_db()
    assert payment.status == Payment.Status.PAID
    assert payment.ref_id == "savepoint-evidence"
    assert payment.verified_at is not None
    assert payment.cart_finalized is False
    assert order.requires_manual_review is True
    assert order.manual_review_reason == LOCAL_CONSTRAINT_REVIEW_REASON
    assert order.stock_reduced is False
    assert product.stock == 10
    assert coupon.used_count == 0
    assert redemption.state == CouponRedemption.State.RESERVED
    assert cart_item.quantity == 2
    assert result.requires_manual_review is True


def test_historical_null_cart_snapshot_never_mutates_current_cart(product):
    user = create_user(24)
    current_item = CartItem.objects.create(
        cart=Cart.objects.create(user=user),
        product=product,
        quantity=3,
    )
    order = create_order(user, product)
    assert order.items.get().cart_item_id_snapshot is None
    payment = create_payment(user, order, "S" * 36)

    finalize_verified_payment(
        payment.id,
        authority=payment.authority,
        verification=verification("historical-cart"),
    )
    finalize_verified_payment(
        payment.id,
        authority=payment.authority,
        verification=verification("historical-cart"),
    )

    payment.refresh_from_db()
    product.refresh_from_db()
    current_item.refresh_from_db()
    assert payment.status == Payment.Status.PAID
    assert payment.cart_finalized is True
    assert product.stock == 9
    assert current_item.quantity == 3


def test_concurrent_orders_competing_for_stock_never_make_stock_negative(product):
    product.stock = 1
    product.save(update_fields=("stock",))
    users = [create_user(8), create_user(9)]
    orders = [create_order(user, product) for user in users]
    payments = [
        create_payment(user, order, authority * 36)
        for user, order, authority in zip(users, orders, ("G", "H"), strict=True)
    ]

    run_concurrently(
        *(
            lambda payment=payment, index=index: finalize_verified_payment(
                payment.id,
                authority=payment.authority,
                verification=verification(f"stock-{index}"),
            )
            for index, payment in enumerate(payments)
        )
    )

    product.refresh_from_db()
    for payment in payments:
        payment.refresh_from_db()
    for order in orders:
        order.refresh_from_db()
    assert product.stock == 0
    assert product.stock >= 0
    assert sum(order.stock_reduced for order in orders) == 1
    assert sum(order.requires_manual_review for order in orders) == 1
    assert all(payment.status == Payment.Status.PAID for payment in payments)


def test_shipping_update_waits_for_and_observes_ineligible_transition(product):
    user = create_user(10)
    order = create_order(user, product)
    order_locked = Event()
    shipping_started = Event()

    def transition():
        close_old_connections()
        try:
            with transaction.atomic():
                locked = Order.objects.select_for_update().get(pk=order.id)
                order_locked.set()
                assert shipping_started.wait(timeout=10)
                locked.status = Order.Status.PROCESSING
                locked.save(update_fields=("status", "updated_at"))
        finally:
            connections.close_all()

    def update_shipping():
        close_old_connections()
        try:
            assert order_locked.wait(timeout=10)
            shipping_started.set()
            try:
                update_order_shipping(
                    order.id,
                    {"recipient_name": "Racing recipient"},
                )
            except ShippingUpdateNotAllowed:
                return "rejected"
            return "updated"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        transition_future = executor.submit(transition)
        shipping_future = executor.submit(update_shipping)
        transition_future.result(timeout=20)
        result = shipping_future.result(timeout=20)

    order.refresh_from_db()
    assert result == "rejected"
    assert order.status == Order.Status.PROCESSING
    assert order.recipient_name == "Concurrent User"


def test_checkout_rolls_back_order_and_coupon_when_one_product_is_invalid(
    product, category, brand
):
    user = create_user(11)
    unavailable = Product.objects.create(
        category=category,
        brand=brand,
        name="Unavailable Toy",
        slug="unavailable-toy",
        description="Unavailable.",
        sku="CONCURRENT-002",
        price=1000,
        stock=0,
        age_group=Product.AgeGroup.THREE_TO_FIVE,
        gender=Product.Gender.UNISEX,
    )
    coupon = Coupon.objects.create(
        code="ROLLBACK",
        discount_type=Coupon.DiscountType.FIXED,
        discount_value=100,
        usage_limit=1,
    )
    cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=cart, product=product, quantity=1)
    CartItem.objects.create(cart=cart, product=unavailable, quantity=1)

    with pytest.raises(ValidationError, match="Insufficient stock"):
        checkout_for(user, coupon_code=coupon.code)

    assert Order.objects.filter(user=user).exists() is False
    assert CouponRedemption.objects.filter(coupon=coupon).exists() is False


def test_checkout_observes_stock_change_committed_while_waiting(product):
    user = create_user(12)
    CartItem.objects.create(
        cart=Cart.objects.create(user=user),
        product=product,
        quantity=1,
    )
    product_locked = Event()
    checkout_started = Event()

    def remove_stock():
        close_old_connections()
        try:
            with transaction.atomic():
                locked = Product.objects.select_for_update().get(pk=product.id)
                product_locked.set()
                assert checkout_started.wait(timeout=10)
                locked.stock = 0
                locked.save(update_fields=("stock",))
        finally:
            connections.close_all()

    def checkout():
        close_old_connections()
        try:
            assert product_locked.wait(timeout=10)
            checkout_started.set()
            with pytest.raises(ValidationError, match="Insufficient stock"):
                checkout_for(user)
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        stock_future = executor.submit(remove_stock)
        checkout_future = executor.submit(checkout)
        stock_future.result(timeout=20)
        checkout_future.result(timeout=20)

    assert Order.objects.filter(user=user).exists() is False


def test_cart_finalization_preserves_line_recreated_after_checkout(product):
    ShippingSettings.load()
    user = create_user(13)
    original_item = CartItem.objects.create(
        cart=Cart.objects.create(user=user),
        product=product,
        quantity=1,
    )
    order = checkout_for(user)
    original_item.delete()
    replacement = CartItem.objects.create(
        cart=user.cart,
        product=product,
        quantity=2,
    )
    payment = create_payment(user, order, "I" * 36)

    finalize_verified_payment(
        payment.id,
        authority=payment.authority,
        verification=verification("replacement-cart-line"),
    )

    replacement.refresh_from_db()
    product.refresh_from_db()
    assert replacement.quantity == 2
    assert product.stock == 9
