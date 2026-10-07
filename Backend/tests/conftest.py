"""Shared fixtures. Repository/DB tests run against a dedicated Postgres
schema (test_swiggy_clone) on the SAME database this project already uses
locally — created fresh and dropped at the end of the test session, so
nothing here ever touches real restaurant/order data. Requires the same
Postgres this project's DATABASE_URL points to be reachable; set
TEST_DATABASE_URL to point elsewhere if that's not what you want.
"""
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from core.models import Base, Category, Restaurant, Item, Order, Coupon

TEST_SCHEMA = "test_swiggy_clone"
BASE_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    os.environ.get("DATABASE_URL", "postgresql://swiggy_user:12345@localhost:5432/swiggy_clone"),
)


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(BASE_DATABASE_URL, connect_args={"options": f"-csearch_path={TEST_SCHEMA}"})
    with eng.connect() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE"))
        conn.execute(text(f"CREATE SCHEMA {TEST_SCHEMA}"))
        conn.commit()

    Base.metadata.create_all(eng)
    yield eng

    with eng.connect() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE"))
        conn.commit()
    eng.dispose()


@pytest.fixture
def db(engine):
    """A session per test, with every table truncated first — tests don't
    depend on each other's data, and this schema exists only for tests."""
    Session = sessionmaker(bind=engine)
    session = Session()
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(text(f"TRUNCATE TABLE {table.name} RESTART IDENTITY CASCADE"))
    session.commit()
    yield session
    session.close()


@pytest.fixture
def category(db):
    cat = Category(name="Recommended", required_day=None)
    db.add(cat)
    db.commit()
    return cat


@pytest.fixture
def gated_category(db):
    """A Wednesday-only category, for day-gating tests."""
    cat = Category(name="WEDNESDAY EXCLUSIVES", required_day="Wednesday")
    db.add(cat)
    db.commit()
    return cat


@pytest.fixture
def restaurant(db):
    r = Restaurant(name="Test Restaurant", rating=4.0, average_cost=200.0, average_time=30, cuisines=["Indian"])
    db.add(r)
    db.commit()
    return r


@pytest.fixture
def item(db, restaurant, category):
    i = Item(
        restaurant_id=restaurant.id,
        category_id=category.id,
        name="Test Item",
        price=100.0,
        veg=True,
        best_seller=False,
    )
    db.add(i)
    db.commit()
    return i


def make_coupon(
    db,
    code="TESTCODE",
    discount_type="flat",
    discount_value=50.0,
    min_order_value=None,
    max_discount=None,
    requires_weekend=False,
    requires_first_order=False,
    restricted_item_names=None,
    active=True,
):
    coupon = Coupon(
        code=code,
        discount_type=discount_type,
        discount_value=discount_value,
        min_order_value=min_order_value,
        max_discount=max_discount,
        requires_weekend=requires_weekend,
        requires_first_order=requires_first_order,
        restricted_item_names=restricted_item_names,
        active=active,
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


def make_order(db, user_id="test-user-1", age=timedelta(0), status="placed"):
    """Helper (not a fixture — tests need different ages/statuses) for a
    minimal order, backdated to test the cancellation window."""
    order = Order(
        id=uuid.uuid4(),
        user_id=user_id,
        total_amount=100.0,
        status=status,
        created_at=datetime.now(timezone.utc) - age,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order
