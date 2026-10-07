import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from core.models import Order, OrderItem, Item

CANCELLATION_WINDOW = timedelta(minutes=10)


def create_order(
    db: Session,
    user_id: str,
    line_items: list[tuple[Item, int]],
    discount_amount: float = 0.0,
    coupon_code: Optional[str] = None,
) -> Order:
    """line_items: list of (Item, quantity) — already-validated, already-loaded
    Item rows, so this only ever writes what the caller confirmed exists.
    discount_amount/coupon_code are likewise assumed pre-validated by the
    caller (main.place_order re-runs validate_coupon server-side) -- this
    function just records the result."""
    raw_total = sum(item.price * qty for item, qty in line_items)
    order = Order(
        user_id=user_id,
        total_amount=raw_total - discount_amount,
        discount_amount=discount_amount,
        applied_coupon_code=coupon_code,
    )
    db.add(order)
    db.flush()  # populate order.id without committing, so children can reference it

    for item, qty in line_items:
        db.add(
            OrderItem(
                order_id=order.id,
                item_id=item.id,
                item_name=item.name,
                restaurant_name=item.restaurant.name,
                price=item.price,
                quantity=qty,
            )
        )

    db.commit()
    db.refresh(order)
    return order


def get_orders_for_user(
    db: Session,
    user_id: str,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[Order]:
    query = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.user_id == user_id)
    )
    if from_date:
        query = query.filter(Order.created_at >= from_date)
    if to_date:
        # to_date is a calendar day; include every order placed during it.
        query = query.filter(Order.created_at < to_date + timedelta(days=1))
    return query.order_by(Order.created_at.desc()).all()


def get_order_by_id(db: Session, user_id: str, order_id: uuid.UUID) -> Optional[Order]:
    return (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == order_id, Order.user_id == user_id)
        .first()
    )


def cancel_order(db: Session, user_id: str, order_id: uuid.UUID) -> tuple[Optional[Order], Optional[str]]:
    """Cancels an order if it's the caller's, not already cancelled or
    delivered, and still within the 10-minute cancellation window.

    Returns (order, error): order is None if it doesn't exist or isn't the
    caller's (caller should treat that as 404, not leak which case it was).
    If order is found but can't be cancelled, order is returned alongside a
    human-readable error explaining why — the caller should treat that as a
    400, not a generic failure."""
    order = get_order_by_id(db, user_id, order_id)
    if order is None:
        return None, None

    if order.status == "cancelled":
        return order, "Order is already cancelled"
    if order.status == "delivered":
        return order, "Cannot cancel an order that has already been delivered"

    age = datetime.now(timezone.utc) - order.created_at
    if age > CANCELLATION_WINDOW:
        return order, "Cancellation window (10 minutes) has expired"

    order.status = "cancelled"
    db.commit()
    db.refresh(order)
    return order, None
