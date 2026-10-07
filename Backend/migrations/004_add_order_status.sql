-- Adds order status ("placed" | "cancelled" | "delivered"), needed so an
-- order can be cancelled within a time window and can't be re-cancelled or
-- cancelled after delivery. Additive only — existing rows all default to
-- "placed", which is accurate: none of them have been cancelled or (there
-- being no delivery tracking in this app) marked delivered.
--
-- Run once, against the swiggy_clone database:
--   psql postgresql://swiggy_user:12345@localhost:5432/swiggy_clone -f Backend/migrations/004_add_order_status.sql

BEGIN;

ALTER TABLE orders ADD COLUMN status TEXT NOT NULL DEFAULT 'placed';

COMMIT;
