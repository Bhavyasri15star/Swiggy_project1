import uuid
from typing import Optional
from sqlalchemy.orm import Session, joinedload, selectinload
from core.models import Restaurant, Item, Category


def get_restaurant_by_id(db: Session, restaurant_id: uuid.UUID) -> Optional[Restaurant]:
    return (
        db.query(Restaurant)
        .options(selectinload(Restaurant.items).selectinload(Item.category))
        .filter(Restaurant.id == restaurant_id)
        .first()
    )


def get_all_restaurants(db: Session, offset: int = 0, limit: Optional[int] = None) -> list[Restaurant]:
    # Explicit ORDER BY -- Postgres gives no row-order guarantee without one,
    # and OFFSET/LIMIT without a stable order can return overlapping or
    # skipped rows across pages.
    query = (
        db.query(Restaurant)
        .options(selectinload(Restaurant.items).selectinload(Item.category))
        .order_by(Restaurant.id)
        .offset(offset)
    )
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def count_restaurants(db: Session) -> int:
    return db.query(Restaurant).count()


def get_item(db: Session, restaurant_id: uuid.UUID, item_id: uuid.UUID) -> Optional[Item]:
    return (
        db.query(Item)
        .options(joinedload(Item.category))
        .filter(Item.restaurant_id == restaurant_id, Item.id == item_id)
        .first()
    )


def create_restaurant(db: Session, data) -> Restaurant:
    restaurant = Restaurant(**data.model_dump())
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return restaurant