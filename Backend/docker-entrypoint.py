"""Container startup for the backend.

Alembic's revision chain here starts mid-history (its earliest revision
ALTERs items.id from int to UUID) because it was added after this project's
schema already existed — it has no "create the schema from scratch"
revision. That's fine against the original dev database (tables already
exist), but a fresh container's Postgres starts empty, and `alembic upgrade
head` would fail immediately trying to ALTER a table that isn't there yet.

So on a fresh database: create all tables directly from the current models
(equivalent end state to running every migration), seed the demo data, then
stamp alembic as head so it agrees the DB is up to date. Against an already-
migrated database (e.g. the original dev one), every step here is a no-op
and this just falls through to starting the server.
"""
import subprocess
import sys
import time

from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError

from core.database import engine, SessionLocal
from core.models import Base, Restaurant, Coupon

MAX_WAIT_SECONDS = 30


def wait_for_db():
    deadline = time.time() + MAX_WAIT_SECONDS
    while True:
        try:
            with engine.connect():
                return
        except OperationalError:
            if time.time() > deadline:
                raise
            print("Waiting for Postgres...", flush=True)
            time.sleep(1)


def ensure_schema():
    Base.metadata.create_all(engine)  # no-op for tables that already exist


def seed_if_empty():
    with SessionLocal() as db:
        has_data = db.query(Restaurant.id).first() is not None
    if has_data:
        print("Restaurants table already has data, skipping seed.", flush=True)
        return
    print("Restaurants table is empty, seeding demo data...", flush=True)
    subprocess.run([sys.executable, "migrate_data.py"], check=True)


def seed_coupons_if_empty():
    """Same self-healing reasoning as seed_if_empty() above -- found empty
    in production once (table existed, zero rows; Base.metadata.create_all()
    silently recreates the empty structure if it's ever missing, but never
    seeds it), so check and restore it on every boot, not just the first."""
    with SessionLocal() as db:
        has_data = db.query(Coupon.id).first() is not None
    if has_data:
        print("Coupons table already has data, skipping seed.", flush=True)
        return
    print("Coupons table is empty, seeding demo coupons...", flush=True)
    subprocess.run([sys.executable, "migrate_coupons.py"], check=True)


def stamp_alembic_head():
    subprocess.run(["alembic", "stamp", "head"], check=True)


def main():
    wait_for_db()
    is_fresh = not inspect(engine).has_table("restaurants")
    ensure_schema()
    if is_fresh:
        seed_if_empty()
        stamp_alembic_head()
    else:
        seed_if_empty()  # still seed an existing-but-empty DB (e.g. a wiped table)
    seed_coupons_if_empty()


if __name__ == "__main__":
    main()
