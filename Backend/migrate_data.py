import sys

from core.database import SessionLocal
from core.models import Restaurant, Category, Item
from restaurant_data import restaurants  # your existing Python list

db = SessionLocal()

# Idempotency guard: docker-entrypoint.py already checks "is this table
# empty" before calling this script, but that check has turned out to be
# unreliable in at least one observed case (a container restart mid-deploy
# — triggered by Render's own port-detection dance — hit a connection-
# state inconsistency where a check moments after a correct "has data"
# result incorrectly concluded "empty"). This script crashing on
# categories' unique constraint when invoked against already-seeded data
# is the actual symptom, not a fluke worth chasing further upstream — so
# make the script itself safe to invoke redundantly, independent of
# whatever convinced the caller to run it.
if db.query(Restaurant.id).first() is not None:
    print("restaurants already has data - migrate_data.py is a no-op here.", flush=True)
    db.close()
    sys.exit(0)

# Step 1: categories
category_names = set()
for r in restaurants:
    for item in r["items"]:
        category_names.add(item["category"])

DAY_GATED = {"WEDNESDAY EXCLUSIVES": "Wednesday"}

category_lookup = {}
for name in category_names:
    cat = Category(name=name, required_day=DAY_GATED.get(name))
    db.add(cat)
    db.flush()
    category_lookup[name] = cat.id

# Step 2: restaurants + items
seen_restaurant_ids = set()
for r in restaurants:
    if r["id"] in seen_restaurant_ids:
        print(f"Skipping duplicate restaurant id {r['id']}: {r['name']}")
        continue
    seen_restaurant_ids.add(r["id"])

    restaurant = Restaurant(
        name=r["name"],
        rating=r["rating"],
        average_cost=r["average_cost"],
        average_time=r["average_time"],
        cuisines=r["cuisines"],
        img_url=r.get("img_url"),
        veg=r["veg"],
        promoted=r.get("promoted", False),
    )
    db.add(restaurant)
    db.flush()

    for item in r["items"]:
        db_item = Item(
            restaurant_id=restaurant.id,
            category_id=category_lookup[item["category"]],
            name=item["name"],
            price=item["price"],
            description=item.get("description"),
            img_url=item.get("img_url"),
            veg=item["veg"],
            best_seller=item["best_seller"],
        )
        db.add(db_item)

db.commit()
db.close()
print("Migration complete.")