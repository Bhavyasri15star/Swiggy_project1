from datetime import datetime
from typing import Optional, Tuple, TypedDict

from sqlalchemy.orm import Session

from core.models import Coupon, Order

WEEKEND_DAYS = ("Saturday", "Sunday")


class CartLine(TypedDict):
    name: str
    price: float
    quantity: int


def get_coupon_by_code(db: Session, code: str) -> Optional[Coupon]:
    return (
        db.query(Coupon)
        .filter(Coupon.code == code, Coupon.active.is_(True))
        .first()
    )


def _matching_lines(coupon: Coupon, cart_items: list[CartLine]) -> list[CartLine]:
    """Every cart line whose name is in the coupon's restricted set. Only
    meaningful when the coupon actually has one -- callers check that first."""
    names = set(coupon.restricted_item_names or [])
    return [line for line in cart_items if line["name"] in names]


def validate_coupon(
    db: Session,
    code: str,
    cart_items: list[CartLine],
    user_id: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Tuple[Optional[Coupon], Optional[str]]:
    """Returns (coupon, error). coupon is None only if the code doesn't exist
    or is inactive -- caller should treat that as "not found". If the coupon
    exists but doesn't apply (below minimum, wrong day, wrong user, no
    qualifying item), it's returned alongside an error explaining why, so
    the caller can show that reason instead of a generic failure.

    cart_items drives everything here -- no separately-passed cart_total,
    so there's no way for it to drift out of sync with the actual items."""
    coupon = get_coupon_by_code(db, code)
    if coupon is None:
        return None, "Invalid coupon code"

    cart_total = sum(line["price"] * line["quantity"] for line in cart_items)

    if coupon.min_order_value is not None and cart_total < coupon.min_order_value:
        return coupon, f"Minimum order value for this coupon is ₹{coupon.min_order_value:.0f}"

    if coupon.requires_weekend:
        day_name = (now or datetime.now()).strftime("%A")
        if day_name not in WEEKEND_DAYS:
            return coupon, "This coupon is only valid on weekends"

    if coupon.requires_first_order:
        if user_id is None or db.query(Order.id).filter(Order.user_id == user_id).first() is not None:
            return coupon, "This coupon is only valid on your first order"

    if coupon.restricted_item_names and not _matching_lines(coupon, cart_items):
        return coupon, f"This coupon only applies to: {', '.join(coupon.restricted_item_names)}"

    return coupon, None


def compute_discount(coupon: Coupon, cart_items: list[CartLine]) -> float:
    """Item-restricted coupons discount ONLY the matching items' subtotal --
    mandatorily, not as an option the caller can skip -- so e.g. "30% off
    desserts" in a cart that also has a ₹900 main course doesn't turn into
    30% off the whole order. Unrestricted coupons discount the full cart,
    same as before."""
    if coupon.restricted_item_names:
        base = sum(line["price"] * line["quantity"] for line in _matching_lines(coupon, cart_items))
    else:
        base = sum(line["price"] * line["quantity"] for line in cart_items)

    if coupon.discount_type == "percent":
        discount = round(base * coupon.discount_value / 100, 2)
        if coupon.max_discount is not None:
            discount = min(discount, coupon.max_discount)
        return discount
    return min(coupon.discount_value, base)  # flat, never exceeds its own base
