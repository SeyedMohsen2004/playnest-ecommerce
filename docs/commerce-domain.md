# Commerce Transaction Boundaries

This document records the database invariants and transaction contracts used by
checkout, payment finalization, cancellation, and shipping mutation. PostgreSQL
row locks are the concurrency boundary; gateway calls are deliberately kept
outside long-lived database transactions.

## State and Snapshot Invariants

- Order state normally progresses from `pending` or `payment_failed` to `paid`,
  then `processing`, `shipped`, and `delivered`. Only `pending` and
  `payment_failed` orders can be normally cancelled.
- A normally cancelled order cannot enter normal fulfilment. A gateway payment
  verified after cancellation is retained as paid evidence and the order is
  flagged for manual review instead of being silently rewritten.
- Payment state is monotonic once paid. Definite failure, cancellation, and
  verification-uncertainty paths never downgrade a paid payment or overwrite
  its verified reference data.
- Product name, unit price, quantity, line total, subtotal, discount, shipping
  cost, and total are server-calculated checkout snapshots. Payment retry and
  finalization do not recalculate them.
- `Order.stock_reduced` is the per-order inventory idempotency marker. Product
  rows are locked and revalidated before the marker and stock changes commit in
  one transaction, so stock cannot become negative or be reduced twice.
- Coupon use is represented once per order. A reservation can be consumed once
  or released once, and `Coupon.used_count` cannot exceed a finite
  `usage_limit`.
- Cart cleanup is an order side effect even when more than one payment attempt
  exists. It happens at most once, and cart rows created after checkout are not
  mistaken for the rows captured by the order.
- Manual review is sticky by default. Only the explicitly recoverable inventory
  and legacy coupon-capacity reasons can be cleared automatically, and only
  after the previously incomplete stock, coupon, order, and cart side effects
  all complete successfully.
- Customer order mutations remain scoped by the API queryset before a domain
  service is invoked. Staff transitions retain their explicit admin rules.

## Canonical Lock Order

Transactions that touch multiple commerce aggregates acquire row locks in this
order:

1. `Order`
2. all related `Payment` rows ordered by primary key
3. the user's `Cart`
4. `Coupon`
5. the order's `CouponRedemption`
6. involved `Product` rows ordered by primary key
7. involved `CartItem` rows ordered by primary key

Checkout has no existing order or payment, so it begins with the cart and then
uses the applicable suffix. It also locks the singleton shipping settings row
before coupon and product locks; no other commerce transition combines that row
with order or payment locks. Shipping-only mutation locks only the order.

The helper that starts from a payment performs a non-locking lookup of its
immutable order foreign key, then locks the order before any payment row. This
avoids the former Payment-to-Order versus Order-to-Payment inversion. A caller
must not acquire a later lock and then call a service that acquires an earlier
one.

## Checkout Transaction

`checkout_cart` owns checkout persistence. Within one atomic transaction it:

1. locks the user's cart;
2. snapshots the current cart item identities;
3. reads the server-managed shipping fee under lock;
4. locks and validates the requested coupon, when present;
5. locks products in primary-key order;
6. locks the snapshotted cart items in primary-key order and rejects a changed
   or missing snapshot;
7. rechecks product existence, active state, stock, and current server price;
8. creates the order, immutable order-item snapshots, and optional coupon
   reservation.

Any failure rolls back the order, items, and reservation together. Checkout
does not clear the cart or reserve stock.

## Coupon Reservation Policy

A limited coupon is reserved at checkout while its coupon row is locked.
Capacity is `used_count` plus active reservations. Unlimited coupons use the
same per-order state without a capacity ceiling.

- Successful verified finalization changes `reserved` to `consumed` and
  increments `used_count` in the same transaction.
- Repeated callbacks and payment retries reuse the order's existing record and
  cannot increment usage again.
- A definite gateway rejection or transport uncertainty retains the
  reservation because the order remains retryable and a late verification can
  still be authoritative.
- Normal order cancellation changes `reserved` to `released`; released capacity
  can then be reserved by another checkout.
- Reservations do not expire automatically. The explicit recovery path for an
  abandoned unpaid order is the normal customer or staff cancellation service.
  Silent time expiry would be unsafe because a delayed verified callback could
  arrive after capacity had been reassigned.
- Historical coupon orders created before the reservation migration are
  handled lazily at payment preparation or finalization. If a verified legacy
  payment cannot safely consume capacity, payment evidence is retained and the
  order enters manual review; its quoted total is never changed.

Before applying the constraint migration to an existing database, an operator
must confirm that no coupon already has `used_count > usage_limit`. The
migration intentionally does not invent reservation states for historical
orders.

## Payment and Inventory Finalization

Payment creation/reuse and local authority persistence use the canonical order,
but the ZarinPal request and verification calls occur without database locks.
After the gateway verifies a payment, an outer transaction records paid
evidence while holding the Order and Payment locks. Coupon, stock, order, and
cart side effects then run in an inner savepoint. A handled local validation or
constraint failure rolls that savepoint back before the order is flagged for
manual review, so verified payment evidence remains committed without partial
local side effects. Connection failures and unexpected programming errors are
not converted into review outcomes.

Insufficient stock, unavailable legacy coupon capacity, a verified payment for
a cancelled order, inconsistent fulfilment state, or multiple verified payment
attempts results in manual review. Verified payment fields remain stored; the
system does not pretend that a successful gateway charge failed. Product stock,
coupon usage, and cart contents are changed only when the corresponding locked
preconditions succeed.

For orders created by the current checkout service, cart cleanup subtracts the
order quantity only from the exact snapshotted cart row. Additional quantity on
that same positively identified row is preserved. If the row was removed and a
new row for the same product was created after checkout, the new row is left
untouched. Historical OrderItems have a `NULL` snapshot and cannot be matched
reliably, so finalization deliberately leaves the current cart row untouched
while still completing the cart-finalization marker. Ambiguous multi-row
snapshot information uses the same safe no-mutation policy. Related payment
rows provide an order-level guard so a late verified retry cannot repeat
cleanup.

## Cancellation and Shipping

`cancel_order` locks the order and every related payment, rereads state, cancels
only pending payments, and releases only a reserved coupon. Repeated service
calls are idempotent. Any paid payment, reduced stock, manual-review flag, or
ineligible order state blocks normal cancellation.

`update_order_shipping` locks and rereads the order before applying validated
fields. It preserves the existing editable states (`pending`,
`payment_failed`, and `paid`) and rejects a concurrent update that loses a race
to an ineligible fulfilment transition.

## Remaining Idempotency Boundaries

- Two simultaneous payment-request HTTP calls can both reach the external
  gateway before one authority wins local persistence. The database retains
  one local authority, but external request issuance is not fully idempotent.
  Gateway calls remain outside long-lived database transactions.
- Checkout is transactionally atomic but does not accept a client idempotency
  key. Repeated submissions can therefore create separate orders.
- Historical OrderItems without a cart snapshot use the safe no-cart-mutation
  policy described above.
- Coupon reservations require explicit customer or staff cancellation and do
  not expire silently.
- Reducing a coupon usage limit below `used_count` is blocked by the database,
  but reducing it below already allocated capacity (`used_count` plus active
  reservations) remains an operator risk requiring manual review.
