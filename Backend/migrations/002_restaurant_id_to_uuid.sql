-- Switches restaurants.id from a serial integer to a UUID primary key,
-- and updates items.restaurant_id (a real foreign key) to match.
--
-- Unlike 001 (items.id, which nothing referenced), this one must preserve
-- the actual restaurant<->item relationships: each item's new restaurant_id
-- is derived by joining on the OLD integer id, not assigned independently.
--
-- Run once, against the swiggy_clone database:
--   psql postgresql://swiggy_user:12345@localhost:5432/swiggy_clone -f Backend/migrations/002_restaurant_id_to_uuid.sql

BEGIN;

-- 1. Give every restaurant a new UUID id alongside its old integer one
ALTER TABLE restaurants ADD COLUMN new_id uuid NOT NULL DEFAULT gen_random_uuid();

-- 2. Give every item the new UUID of ITS restaurant (preserves the relationship)
ALTER TABLE items ADD COLUMN new_restaurant_id uuid;
UPDATE items SET new_restaurant_id = r.new_id
FROM restaurants r
WHERE items.restaurant_id = r.id;

-- Safety check: abort if any item didn't get mapped (would indicate an
-- orphaned restaurant_id that doesn't exist in restaurants — shouldn't
-- happen given the existing FK, but don't proceed silently if it did)
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM items WHERE new_restaurant_id IS NULL) THEN
    RAISE EXCEPTION 'Some items did not get a new_restaurant_id — aborting migration';
  END IF;
END $$;

ALTER TABLE items ALTER COLUMN new_restaurant_id SET NOT NULL;

-- 3. Drop the FK first — it depends on restaurants_pkey, so the old pkey
--    can't be dropped while it still exists
ALTER TABLE items DROP CONSTRAINT items_restaurant_id_fkey;

-- 4. Swap the primary key on restaurants: drop old int id, promote new_id
ALTER TABLE restaurants DROP CONSTRAINT restaurants_pkey;
ALTER TABLE restaurants DROP COLUMN id;
ALTER TABLE restaurants RENAME COLUMN new_id TO id;
ALTER TABLE restaurants ADD PRIMARY KEY (id);
ALTER TABLE restaurants ALTER COLUMN id SET DEFAULT gen_random_uuid();

-- 5. Swap the FK column on items: drop old int restaurant_id, promote new one
ALTER TABLE items DROP COLUMN restaurant_id;
ALTER TABLE items RENAME COLUMN new_restaurant_id TO restaurant_id;
ALTER TABLE items ADD CONSTRAINT items_restaurant_id_fkey
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id);

COMMIT;
