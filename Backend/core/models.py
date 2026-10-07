import uuid

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    required_day = Column(String, nullable=True)  # e.g. "Wednesday", NULL if not gated


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    rating = Column(Float)
    average_cost = Column(Float)
    average_time = Column(Integer)
    cuisines = Column(ARRAY(String))
    img_url = Column(String)
    veg = Column(Boolean, default=False)
    promoted = Column(Boolean, default=False)

    items = relationship("Item", back_populates="restaurant", cascade="all, delete-orphan")


class Item(Base):
    __tablename__ = "items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id"), index=True,nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), index=True, nullable=False)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String)
    img_url = Column(String)
    veg = Column(Boolean, default=False)
    best_seller = Column(Boolean, default=False)

    restaurant = relationship("Restaurant", back_populates="items")
    category = relationship("Category")


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False, index=True)
    discount_type = Column(String, nullable=False)  # "flat" | "percent"
    discount_value = Column(Float, nullable=False)
    min_order_value = Column(Float, nullable=True)  # NULL = no minimum
    max_discount = Column(Float, nullable=True)  # caps a percent discount; NULL = uncapped
    requires_weekend = Column(Boolean, nullable=False, default=False, server_default="false")
    requires_first_order = Column(Boolean, nullable=False, default=False, server_default="false")
    restricted_item_names = Column(ARRAY(String), nullable=True)  # NULL = applies to any item
    active = Column(Boolean, nullable=False, default=True, server_default="true")


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Conceptually references auth.users(id) — enforced at the DB level by
    # the migration's REFERENCES auth.users(id), NOT by a SQLAlchemy
    # ForeignKey() here. auth.users is owned by AuthService (Prisma), not
    # mapped as a SQLAlchemy table in this app, and SQLAlchemy needs to
    # resolve every ForeignKey() target against a table it knows about
    # whenever it sorts tables for a flush — pointing one at an unmapped
    # table raises NoReferencedTableError the moment an Order is inserted.
    # Prisma's `String @default(uuid())` also stores this as plain text
    # (not Postgres's native uuid type), even though the values are
    # UUID-shaped, hence String here to match.
    user_id = Column(String, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    total_amount = Column(Float, nullable=False)
    # "placed" | "cancelled" | "delivered". Nothing currently transitions an
    # order to "delivered" (there's no delivery simulation/tracking in this
    # app) — that value exists so cancellation logic is correct for when
    # such a mechanism gets added, not because it's reachable today.
    status = Column(String, nullable=False, default="placed", server_default="placed")
    applied_coupon_code = Column(String, nullable=True)
    discount_amount = Column(Float, nullable=False, default=0.0, server_default="0")

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), index=True, nullable=False)
    item_id = Column(UUID(as_uuid=True), ForeignKey("items.id"), nullable=True)
    # Snapshots, not live references — survive the underlying item's price
    # (or its restaurant) changing or being removed later, so past orders
    # don't silently change.
    item_name = Column(String, nullable=False)
    restaurant_name = Column(String, nullable=True)  # NULL only for pre-existing rows
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")