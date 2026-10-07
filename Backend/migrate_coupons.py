"""Idempotent coupon seeding -- same pattern as migrate_data.py.

Exists because the coupons table was found empty in production once
already (most likely: the table itself got dropped somehow, and a later
container restart's Base.metadata.create_all() silently recreated the
empty structure with no data, since schema creation never seeds rows --
only this script does, and only docker-entrypoint.py was calling it for
restaurants, not coupons). Running this on every container boot (not
just the first one) makes coupons self-healing the same way restaurants
already were.
"""
import sys

from core.database import SessionLocal
from core.models import Coupon

db = SessionLocal()

if db.query(Coupon.id).first() is not None:
    print("coupons already has data - migrate_coupons.py is a no-op here.", flush=True)
    db.close()
    sys.exit(0)

COUPONS = [
    {"code": "FLAT50", "discount_type": "flat", "discount_value": 50, "min_order_value": 199},
    {"code": "BIGSAVER", "discount_type": "flat", "discount_value": 125, "min_order_value": 349},
    {
        "code": "TRYNEW", "discount_type": "percent", "discount_value": 50,
        "max_discount": 100, "requires_first_order": True,
    },
    {"code": "FREEDEL", "discount_type": "flat", "discount_value": 39},
    {
        "code": "WEEKEND20", "discount_type": "percent", "discount_value": 20,
        "max_discount": 150, "requires_weekend": True,
    },
    {
        "code": "SWEETTOOTH", "discount_type": "percent", "discount_value": 30,
        "max_discount": 60, "restricted_item_names": ["Coffee Mousse Cake", "Choco Mud Pie"],
    },
]

for c in COUPONS:
    db.add(Coupon(**c))

db.commit()
db.close()
print("Coupon seed complete.", flush=True)
