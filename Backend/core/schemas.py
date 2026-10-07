from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str  # UUID, stringified before validation (see main._restaurant_to_dict)
    name: str
    price: float
    description: str | None = None
    img_url: str | None = None
    veg: bool
    best_seller: bool
    category: str  


class RestaurantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str  # UUID, stringified before validation (see main._restaurant_to_dict)
    name: str
    rating: float
    average_cost: float
    average_time: int
    cuisines: list[str]
    img_url: str | None = None
    veg: bool
    promoted: bool
    items: list[ItemOut] = []


class RestaurantCreate(BaseModel):
    name: str
    rating: float
    average_cost: float
    average_time: int
    cuisines: list[str]
    img_url: str | None = None
    veg: bool = False
    promoted: bool = False


class CartItemRef(BaseModel):
    # Kept as plain strings (not uuid.UUID) so main.validate_cart can parse
    # and validate them manually before opening a DB session — see
    # main._parse_uuid for why that matters.
    restaurant_id: str
    item_id: str


class OrderItemCreate(BaseModel):
    # Also plain str for the same reason as CartItemRef above.
    item_id: str
    quantity: int = 1


class OrderCreate(BaseModel):
    items: list[OrderItemCreate]
    coupon_code: str | None = None


class CouponCartItem(BaseModel):
    name: str
    price: float
    quantity: int = 1


class CouponValidateRequest(BaseModel):
    code: str
    cart_items: list[CouponCartItem]


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item_name: str
    restaurant_name: str | None = None
    price: float
    quantity: int


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    total_amount: float
    status: str
    applied_coupon_code: str | None = None
    discount_amount: float = 0.0
    items: list[OrderItemOut] = []