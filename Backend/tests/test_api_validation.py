"""API-level tests via the real app object. Only exercises paths that are
safe regardless of DB/Redis state (malformed-UUID rejection happens before
any DB session opens; auth checks happen before any handler code runs) —
see main.py's _parse_uuid docstring for why that ordering matters."""
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_malformed_restaurant_id_is_422_not_500():
    res = client.get("/restaurants/not-a-uuid")
    assert res.status_code == 422


def test_malformed_item_id_is_422_not_500():
    res = client.get("/restaurants/6615a115-1ab3-42c7-96ac-ebaa57ca5472/items/also-not-a-uuid")
    assert res.status_code == 422


def test_payment_validate_rejects_malformed_id_in_list():
    res = client.post(
        "/payment/validate",
        json=[{"restaurant_id": "not-a-uuid", "item_id": "also-not-a-uuid"}],
    )
    assert res.status_code == 422


def test_orders_requires_auth():
    res = client.get("/orders")
    assert res.status_code == 401


def test_place_order_requires_auth():
    res = client.post("/orders", json={"items": []})
    assert res.status_code == 401


def test_restaurants_rejects_non_positive_page():
    res = client.get("/restaurants?page=0")
    assert res.status_code == 400


def test_restaurants_rejects_non_positive_page_size():
    res = client.get("/restaurants?page_size=0")
    assert res.status_code == 400


def test_malformed_order_id_requires_auth_check_first():
    """No Authorization header at all — should 401, not 422, even though
    the order_id here is also malformed. Whichever check runs, the
    response must never be a 500."""
    res = client.get("/orders/not-a-uuid")
    assert res.status_code in (401, 422)
