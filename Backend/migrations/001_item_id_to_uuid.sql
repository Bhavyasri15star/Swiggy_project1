-- Switches items.id from a serial integer to a UUID primary key.
-- Safe to run on live data: nothing else has a foreign key to items.id
-- (verified via information_schema.table_constraints), so every existing
-- row keeps all its data (name, price, restaurant_id, category_id, ...)
-- and is only assigned a fresh random id.
--
-- Run once, against the swiggy_clone database:
--   psql postgresql://swiggy_user:12345@localhost:5432/swiggy_clone -f Backend/migrations/001_item_id_to_uuid.sql

BEGIN;

ALTER TABLE items ALTER COLUMN id DROP DEFAULT;
ALTER TABLE items ALTER COLUMN id TYPE uuid USING gen_random_uuid();
ALTER TABLE items ALTER COLUMN id SET DEFAULT gen_random_uuid();

COMMIT;
