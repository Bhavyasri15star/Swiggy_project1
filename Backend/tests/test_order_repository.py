"""cancel_order carries the actual business rule (10-minute window, status
gating) — the highest-value thing in this codebase to lock in with tests,
since a regression here means either silently un-cancellable orders or
orders cancellable long after they shouldn't be."""
from datetime import timedelta

from repositories.order_repository import cancel_order, create_order, CANCELLATION_WINDOW
from tests.conftest import make_order


def test_create_order_snapshots_restaurant_name(db, restaurant, item):
    order = create_order(db, "test-user-1", [(item, 2)])
    assert order.items[0].restaurant_name == restaurant.name


def test_cancel_within_window_succeeds(db):
    order = make_order(db, age=timedelta(minutes=2))
    result, error = cancel_order(db, order.user_id, order.id)
    assert error is None
    assert result.status == "cancelled"


def test_cancel_after_window_fails(db):
    order = make_order(db, age=CANCELLATION_WINDOW + timedelta(minutes=1))
    result, error = cancel_order(db, order.user_id, order.id)
    assert result is not None  # order exists — this is a 400, not a 404
    assert "expired" in error.lower()
    assert result.status == "placed"  # unchanged


def test_cancel_already_cancelled_fails(db):
    order = make_order(db, age=timedelta(minutes=1), status="cancelled")
    result, error = cancel_order(db, order.user_id, order.id)
    assert result is not None
    assert "already cancelled" in error.lower()


def test_cancel_delivered_order_fails(db):
    order = make_order(db, age=timedelta(minutes=1), status="delivered")
    result, error = cancel_order(db, order.user_id, order.id)
    assert result is not None
    assert "delivered" in error.lower()


def test_cancel_nonexistent_order_returns_none_none(db):
    """None, None (not None, "some error") is deliberate — main.py treats
    this as a 404, distinct from the 400s above for a real order that just
    can't be cancelled right now (see cancel_order's docstring)."""
    import uuid

    result, error = cancel_order(db, "test-user-1", uuid.uuid4())
    assert result is None
    assert error is None


def test_cancel_another_users_order_returns_none_none(db):
    """Same 404-not-400 treatment for someone else's order — must not leak
    that the order exists at all to a caller who doesn't own it."""
    order = make_order(db, user_id="owner", age=timedelta(minutes=1))
    result, error = cancel_order(db, "someone-else", order.id)
    assert result is None
    assert error is None
