import logging
import os
import uuid
from datetime import date, datetime

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session
import redis
from redis.backoff import NoBackoff
from redis.retry import Retry
import json

logger = logging.getLogger("swiggy_backend")

from core.auth import get_current_user
from core.database import SessionLocal, get_db
from core.models import Item
from core.schemas import (
    RestaurantOut,
    RestaurantCreate,
    CartItemRef,
    OrderCreate,
    OrderOut,
    CouponValidateRequest,
)
from repositories import (
    get_restaurant_by_id,
    get_all_restaurants,
    count_restaurants,
    get_item,
    create_restaurant,
    create_order,
    get_orders_for_user,
    get_order_by_id,
    cancel_order,
    validate_coupon,
    compute_discount,
)
from middleware.rate_limit import RateLimitMiddleware, TimingMiddleware

app = FastAPI()

# Middleware order matters: Starlette makes the LAST-added middleware the
# OUTERMOST layer, so add these two before CORS — otherwise a request
# short-circuited by RateLimitMiddleware (a 429) would skip CORS entirely,
# and the browser would report it as a CORS failure instead of a 429 the
# frontend could actually read.
app.add_middleware(
    RateLimitMiddleware,
    limit=int(os.environ.get("RATE_LIMIT", "100")),
    window_seconds=int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "60")),
)
app.add_middleware(TimingMiddleware)

# Comma-separated list of extra allowed origins, e.g. for LAN demos:
#   CORS_ORIGINS=http://192.168.1.23:3000
_extra_origins = [
    o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        *_extra_origins,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Without these, an unhandled exception falls through to Starlette's default
# handler, which returns a PLAIN TEXT "Internal Server Error" body — every
# other response here is JSON, so the frontend's `res.json()` throws a
# confusing secondary parse error on top of the real failure. These give a
# consistent JSON shape and distinguish "the database is unreachable, retry
# later" from "something is actually broken," while logging full detail
# server-side and never leaking it to the client. HTTPException (used for
# every intentional 4xx above) is unaffected — FastAPI's own handler for it
# takes precedence over these broader ones.
@app.exception_handler(OperationalError)
async def handle_operational_error(request: Request, exc: OperationalError):
    """Postgres unreachable/connection dropped/timed out."""
    logger.error("Database connection error on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=503,
        content={"detail": "Database temporarily unavailable — please try again shortly"},
    )


@app.exception_handler(IntegrityError)
async def handle_integrity_error(request: Request, exc: IntegrityError):
    """Constraint violation — e.g. a duplicate/foreign-key conflict."""
    logger.error("Database integrity error on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=409, content={"detail": "Conflicting data"})


@app.exception_handler(SQLAlchemyError)
async def handle_sqlalchemy_error(request: Request, exc: SQLAlchemyError):
    """Any other database error not covered above."""
    logger.error("Database error on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=500, content={"detail": "A database error occurred"})


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    """Last resort for anything else — a bug, a third-party library error,
    whatever. Logs the full exception so it's debuggable, but the client
    only ever sees a generic message, never internals or a stack trace."""
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

# Short timeouts, zero retries, so a dead/unreachable Redis fails fast (a
# couple seconds) instead of hanging the request indefinitely — this
# environment's Redis (WSL-hosted) has repeatedly gone down mid-session.
# retries=0 matters as much as the timeouts: redis-py's default client
# retries a failed connection several times, so without disabling that, a
# 2s timeout still multiplies into 10+ seconds before finally giving up.
r = redis.Redis(
    host=os.environ.get("REDIS_HOST", "localhost"),
    port=int(os.environ.get("REDIS_PORT", "6379")),
    db=0, decode_responses=True,
    socket_connect_timeout=2, socket_timeout=2,
    retry=Retry(NoBackoff(), retries=0), retry_on_error=[],
)

DEFAULT_TTL = 300  # 5 minutes


def _cache_get(key: str) -> str | None:
    """Redis is a performance optimization, not a hard dependency — any
    Redis error is treated as a cache miss so the caller falls through to
    querying Postgres directly instead of failing the whole request."""
    try:
        return r.get(key)
    except redis.exceptions.RedisError:
        return None


def _cache_set(key: str, value: str, ex: int) -> None:
    try:
        r.set(key, value, ex=ex)
    except redis.exceptions.RedisError:
        pass  # best-effort cache write; the DB write already succeeded


def _cache_delete(key: str) -> None:
    try:
        r.delete(key)
    except redis.exceptions.RedisError:
        pass


def _cache_delete_pattern(pattern: str) -> None:
    """For cache keys that vary by query params (e.g. one per
    page/page_size combination) -- a single known key isn't enough to
    invalidate all of them."""
    try:
        for key in r.scan_iter(match=pattern):
            r.delete(key)
    except redis.exceptions.RedisError:
        pass


def _is_available_today(category_name: str, required_day: str | None) -> bool:
    return required_day is None or datetime.now().strftime("%A") == required_day


def _parse_uuid(value: str, field_name: str) -> uuid.UUID:
    """Validate a path/body value as a UUID before any DB session is opened.
    FastAPI resolves Depends(get_db) alongside path/body validation rather
    than after it succeeds, so typing a param as `uuid.UUID` directly still
    opens a real DB connection for garbage input. Parsing manually first,
    ahead of any Depends(get_db), avoids that."""
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        raise HTTPException(status_code=422, detail=f"'{value}' is not a valid UUID for {field_name}")


def _restaurant_to_dict(restaurant, today_only: bool = True) -> dict:
    """Serialize ORM restaurant -> dict, flattening category and applying day-gating."""
    out = RestaurantOut.model_validate(
        {
            **restaurant.__dict__,
            "id": str(restaurant.id),
            "items": [
                {**item.__dict__, "id": str(item.id), "category": item.category.name}
                for item in restaurant.items
                if not today_only or _is_available_today(item.category.name, item.category.required_day)
            ],
        }
    )
    return out.model_dump()


def _order_to_dict(order) -> dict:
    """Serialize ORM order -> dict, matching _restaurant_to_dict's style."""
    out = OrderOut.model_validate(
        {
            **order.__dict__,
            "id": str(order.id),
            "items": order.items,
        }
    )
    return out.model_dump(mode="json")  # mode="json" so created_at -> ISO string, not a datetime object


@app.get("/")
def home():
    return {"message": "FastAPI is running"}


@app.get("/me")
def whoami(user: dict = Depends(get_current_user)):
    """Demo protected endpoint proving FastAPI can verify a JWT issued by
    AuthService (Express + Prisma). Not required by any existing route —
    browsing restaurants stays anonymous, as before."""
    return {"user": {"id": user["sub"], "email": user["email"], "name": user.get("name")}}


MAX_PAGE_SIZE = 100


@app.get("/restaurants")
def list_restaurants(page: int = 1, page_size: int = 20, db: Session = Depends(get_db)):
    if page < 1 or page_size < 1:
        raise HTTPException(status_code=400, detail="page and page_size must be at least 1")
    page_size = min(page_size, MAX_PAGE_SIZE)

    cache_key = f"restaurants:page:{page}:size:{page_size}"
    cached = _cache_get(cache_key)
    if cached:
        return json.loads(cached)

    total = count_restaurants(db)
    restaurants = get_all_restaurants(db, offset=(page - 1) * page_size, limit=page_size)
    result = {
        "items": [_restaurant_to_dict(rest) for rest in restaurants],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
    _cache_set(cache_key, json.dumps(result), DEFAULT_TTL)
    return result


@app.get("/restaurants/{restaurant_id}")
def get_one_restaurant(restaurant_id: str):
    rid = _parse_uuid(restaurant_id, "restaurant_id")  # validated before any DB session opens

    cache_key = f"restaurant:{rid}"
    cached = _cache_get(cache_key)
    if cached:
        return json.loads(cached)

    with SessionLocal() as db:
        restaurant = get_restaurant_by_id(db, rid)
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        result = _restaurant_to_dict(restaurant)

    _cache_set(cache_key, json.dumps(result), DEFAULT_TTL)
    return result


@app.get("/restaurants/{restaurant_id}/items/{item_id}")
def get_single_item(restaurant_id: str, item_id: str):
    rid = _parse_uuid(restaurant_id, "restaurant_id")
    iid = _parse_uuid(item_id, "item_id")  # both validated before any DB session opens

    with SessionLocal() as db:
        item = get_item(db, rid, iid)
        if item is None:
            raise HTTPException(status_code=404, detail="Item not found")
        if not _is_available_today(item.category.name, item.category.required_day):
            raise HTTPException(status_code=404, detail="Item not available today")
        return {**item.__dict__, "category": item.category.name}


@app.post("/restaurants")
def add_restaurant(restaurant: RestaurantCreate, db: Session = Depends(get_db)):
    created = create_restaurant(db, restaurant)
    _cache_delete_pattern("restaurants:page:*")
    return {"message": "Restaurant created successfully", "restaurant": created.id}


@app.post("/payment/validate")
def validate_cart(cart_items: list[CartItemRef]):
    # Validate every id up front, before opening a DB session — same reasoning
    # as _parse_uuid's docstring: one malformed id anywhere in the list would
    # otherwise still trigger a DB connection before the request is rejected.
    parsed = [
        (_parse_uuid(ref.restaurant_id, "restaurant_id"), _parse_uuid(ref.item_id, "item_id"))
        for ref in cart_items
    ]

    valid, removed = [], []
    with SessionLocal() as db:
        for ref, (rid, iid) in zip(cart_items, parsed):
            item = get_item(db, rid, iid)
            if item is None:
                removed.append(ref.item_id)
            elif not _is_available_today(item.category.name, item.category.required_day):
                removed.append(ref.item_id)
            else:
                valid.append(ref.item_id)
    return {"valid_items": valid, "removed_items": removed}


@app.post("/coupons/validate")
def validate_coupon_endpoint(payload: CouponValidateRequest, user: dict = Depends(get_current_user)):
    """Checks a coupon code against a cart (sent by the frontend before
    checkout, purely so it can show the discount/rejection reason inline --
    the real, trusted check happens again in place_order itself)."""
    cart_items = [{"name": i.name, "price": i.price, "quantity": i.quantity} for i in payload.cart_items]
    with SessionLocal() as db:
        coupon, error = validate_coupon(db, payload.code, cart_items, user_id=user["sub"])
        if coupon is None:
            raise HTTPException(status_code=404, detail=error)
        if error:
            raise HTTPException(status_code=400, detail=error)
        return {
            "valid": True,
            "code": coupon.code,
            "discount_amount": compute_discount(coupon, cart_items),
        }


@app.post("/orders", status_code=201, response_model=OrderOut)
def place_order(order: OrderCreate, user: dict = Depends(get_current_user)):
    if not order.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    # Validate every item id and quantity up front, before opening a DB
    # session — same reasoning as _parse_uuid's docstring. user_id (the
    # JWT's sub claim) is stored as plain text (matching auth.users.id's
    # actual column type — see core/models.py's comment on Order.user_id),
    # so it's used as-is rather than parsed into a uuid.UUID object.
    user_id = user["sub"]
    parsed_items = [(_parse_uuid(li.item_id, "item_id"), li.quantity) for li in order.items]
    for item_id, qty in parsed_items:
        if qty < 1:
            raise HTTPException(status_code=400, detail=f"Quantity for item {item_id} must be at least 1")

    with SessionLocal() as db:
        line_items = []
        for item_id, qty in parsed_items:
            item = db.query(Item).filter(Item.id == item_id).first()
            if item is None:
                raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
            if not _is_available_today(item.category.name, item.category.required_day):
                raise HTTPException(status_code=400, detail=f"Item {item_id} is not available today")
            line_items.append((item, qty))

        discount_amount = 0.0
        applied_code = None
        if order.coupon_code:
            cart_items = [{"name": item.name, "price": item.price, "quantity": qty} for item, qty in line_items]
            coupon, error = validate_coupon(db, order.coupon_code, cart_items, user_id=user_id)
            if coupon is None or error:
                raise HTTPException(status_code=400, detail=error or "Invalid coupon code")
            discount_amount = compute_discount(coupon, cart_items)
            applied_code = coupon.code

        created = create_order(db, user_id, line_items, discount_amount=discount_amount, coupon_code=applied_code)
        return _order_to_dict(created)


@app.get("/orders", response_model=list[OrderOut])
def list_orders(
    from_date: date | None = None,
    to_date: date | None = None,
    user: dict = Depends(get_current_user),
):
    """List the current user's own past orders. Optional ?from_date=&to_date=
    (YYYY-MM-DD) filter by the calendar day the order was placed, inclusive
    on both ends."""
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=400, detail="from_date must not be after to_date")

    user_id = user["sub"]
    with SessionLocal() as db:
        orders = get_orders_for_user(db, user_id, from_date, to_date)
        return [_order_to_dict(o) for o in orders]


@app.get("/orders/{order_id}", response_model=OrderOut)
def get_one_order(order_id: str, user: dict = Depends(get_current_user)):
    oid = _parse_uuid(order_id, "order_id")  # validated before any DB session opens
    user_id = user["sub"]

    with SessionLocal() as db:
        order = get_order_by_id(db, user_id, oid)
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")
        return _order_to_dict(order)


@app.post("/orders/{order_id}/cancel", response_model=OrderOut)
def cancel_one_order(order_id: str, user: dict = Depends(get_current_user)):
    """Cancels an order — only allowed within 10 minutes of it being placed,
    and only while it's still "placed" (not already cancelled or delivered)."""
    oid = _parse_uuid(order_id, "order_id")  # validated before any DB session opens
    user_id = user["sub"]

    with SessionLocal() as db:
        order, error = cancel_order(db, user_id, oid)
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")
        if error:
            raise HTTPException(status_code=400, detail=error)
        return _order_to_dict(order)