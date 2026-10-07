"""validate_coupon/compute_discount take a structured cart (name/price/
quantity per line) rather than a separately-passed total, so there's no way
for a discount to be computed against a cart total that doesn't match the
items it's supposedly discounting -- this file pins down min_order_value,
weekend, first-order, and item-restricted rules, plus the one real
correctness bug an item-restricted coupon can have: discounting the WHOLE
cart instead of just the matching items."""
from datetime import datetime, timedelta

from repositories.coupon_repository import validate_coupon, compute_discount
from tests.conftest import make_coupon, make_order

A_SATURDAY = datetime(2026, 1, 3)
A_MONDAY = datetime(2026, 1, 5)


def cart(*lines):
    """lines: (name, price, quantity) tuples -> the dict shape validate_coupon/compute_discount expect."""
    return [{"name": n, "price": p, "quantity": q} for n, p, q in lines]


def test_coupon_at_or_above_minimum_applies(db):
    coupon = make_coupon(db, code="BIGSAVER", discount_value=125.0, min_order_value=349.0)
    result, error = validate_coupon(db, "BIGSAVER", cart(("Item", 349.0, 1)))
    assert error is None
    assert result.id == coupon.id


def test_coupon_below_minimum_rejected(db):
    make_coupon(db, code="BIGSAVER", discount_value=125.0, min_order_value=349.0)
    result, error = validate_coupon(db, "BIGSAVER", cart(("Item", 348.99, 1)))
    assert result is not None  # coupon exists — this is "doesn't apply", not "not found"
    assert "minimum order value" in error.lower()


def test_coupon_with_no_minimum_always_applies(db):
    make_coupon(db, code="FREEDEL", discount_value=39.0, min_order_value=None)
    result, error = validate_coupon(db, "FREEDEL", cart(("Item", 1.0, 1)))
    assert error is None
    assert result is not None


def test_unknown_code_returns_none_none(db):
    result, error = validate_coupon(db, "DOESNOTEXIST", cart(("Item", 500.0, 1)))
    assert result is None
    assert error is not None


def test_inactive_coupon_treated_as_unknown(db):
    """Must not leak that an inactive/retired code ever existed -- same
    404-not-400 reasoning as cancel_order's nonexistent-order case."""
    make_coupon(db, code="EXPIRED", discount_value=50.0, active=False)
    result, error = validate_coupon(db, "EXPIRED", cart(("Item", 500.0, 1)))
    assert result is None
    assert error is not None


def test_compute_discount_flat_never_exceeds_cart_total(db):
    coupon = make_coupon(db, discount_type="flat", discount_value=125.0)
    assert compute_discount(coupon, cart(("Item", 349.0, 1))) == 125.0
    assert compute_discount(coupon, cart(("Item", 50.0, 1))) == 50.0  # capped, not negative total


def test_compute_discount_percent(db):
    coupon = make_coupon(db, discount_type="percent", discount_value=20.0)
    assert compute_discount(coupon, cart(("Item", 200.0, 1))) == 40.0


def test_compute_discount_percent_capped_by_max_discount(db):
    coupon = make_coupon(db, discount_type="percent", discount_value=50.0, max_discount=100.0)
    assert compute_discount(coupon, cart(("Item", 1000.0, 1))) == 100.0  # would be 500 uncapped


def test_weekend_coupon_rejected_on_a_weekday(db):
    make_coupon(db, code="WEEKEND20", requires_weekend=True)
    result, error = validate_coupon(db, "WEEKEND20", cart(("Item", 500.0, 1)), now=A_MONDAY)
    assert result is not None
    assert "weekend" in error.lower()


def test_weekend_coupon_applies_on_a_weekend(db):
    make_coupon(db, code="WEEKEND20", requires_weekend=True)
    result, error = validate_coupon(db, "WEEKEND20", cart(("Item", 500.0, 1)), now=A_SATURDAY)
    assert error is None


def test_first_order_coupon_applies_with_no_prior_orders(db):
    make_coupon(db, code="TRYNEW", requires_first_order=True)
    result, error = validate_coupon(db, "TRYNEW", cart(("Item", 500.0, 1)), user_id="brand-new-user")
    assert error is None


def test_first_order_coupon_rejected_with_a_prior_order(db):
    make_coupon(db, code="TRYNEW", requires_first_order=True)
    make_order(db, user_id="repeat-user", age=timedelta(days=1))
    result, error = validate_coupon(db, "TRYNEW", cart(("Item", 500.0, 1)), user_id="repeat-user")
    assert result is not None
    assert "first order" in error.lower()


def test_first_order_coupon_rejected_without_a_user_id(db):
    """requires_first_order with no user_id at all (e.g. a preview call that
    somehow omits it) must fail closed, not silently skip the check."""
    make_coupon(db, code="TRYNEW", requires_first_order=True)
    result, error = validate_coupon(db, "TRYNEW", cart(("Item", 500.0, 1)), user_id=None)
    assert result is not None
    assert "first order" in error.lower()


def test_item_restricted_coupon_applies_when_cart_has_a_matching_item(db):
    make_coupon(db, code="SWEETTOOTH", restricted_item_names=["Coffee Mousse Cake", "Choco Mud Pie"])
    result, error = validate_coupon(
        db, "SWEETTOOTH", cart(("Choco Mud Pie", 128.57, 1), ("Pepsi PET", 57.14, 1))
    )
    assert error is None


def test_item_restricted_coupon_rejected_without_a_matching_item(db):
    make_coupon(db, code="SWEETTOOTH", restricted_item_names=["Coffee Mousse Cake", "Choco Mud Pie"])
    result, error = validate_coupon(db, "SWEETTOOTH", cart(("Pepsi PET", 57.14, 1)))
    assert result is not None
    assert "coffee mousse cake" in error.lower()


def test_item_restricted_discount_applies_only_to_matching_items(db):
    """The actual bug this guards against: a cart with one ₹931 main course
    and one ₹128 dessert, SWEETTOOTH (30% off desserts) applied -- the
    discount must be 30% of the dessert ALONE (38.57), never 30% of the
    whole cart (which would be capped at max_discount=60 and look
    "correct" by coincidence at this exact cap value, so the cap is
    deliberately left high enough here to tell the two apart)."""
    coupon = make_coupon(
        db,
        code="SWEETTOOTH",
        discount_type="percent",
        discount_value=30.0,
        max_discount=1000.0,  # effectively uncapped, so the bug can't hide behind the cap
        restricted_item_names=["Coffee Mousse Cake", "Choco Mud Pie"],
    )
    mixed_cart = cart(("Super 6s Bucket Meal", 931.43, 1), ("Coffee Mousse Cake", 128.57, 1))
    discount = compute_discount(coupon, mixed_cart)
    assert discount == 38.57  # 30% of 128.57 alone
    assert discount != round((931.43 + 128.57) * 0.30, 2)  # not 30% of the whole cart


def test_item_restricted_discount_sums_multiple_matching_lines(db):
    coupon = make_coupon(
        db,
        code="SWEETTOOTH",
        discount_type="percent",
        discount_value=30.0,
        max_discount=1000.0,
        restricted_item_names=["Coffee Mousse Cake", "Choco Mud Pie"],
    )
    mixed_cart = cart(
        ("Super 6s Bucket Meal", 931.43, 1),
        ("Coffee Mousse Cake", 128.57, 1),
        ("Choco Mud Pie", 128.57, 2),
    )
    # 30% of (128.57 + 128.57*2) = 30% of 385.71
    assert compute_discount(coupon, mixed_cart) == round(385.71 * 0.30, 2)
