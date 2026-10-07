-- Order history storage. Two new tables, additive only — nothing existing
-- is touched, so this is safe to run without a backup pass first.
--
-- orders.user_id references auth.users(id) — a cross-schema FK into the
-- table AuthService (Prisma) owns in the same swiggy_clone database.
-- That column is TEXT (Prisma's `String @default(uuid())` doesn't use
-- Postgres's native uuid type, despite the values being UUID-shaped), so
-- user_id has to be TEXT here too — a uuid column can't FK into a text one.
--
-- Run once, against the swiggy_clone database:
--   psql postgresql://swiggy_user:12345@localhost:5432/swiggy_clone -f Backend/migrations/003_create_orders.sql

BEGIN;

CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL REFERENCES auth.users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    total_amount DOUBLE PRECISION NOT NULL
);
CREATE INDEX ix_orders_user_id ON orders (user_id);
CREATE INDEX ix_orders_created_at ON orders (created_at);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    item_id UUID REFERENCES items(id),
    item_name TEXT NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    quantity INTEGER NOT NULL
);
CREATE INDEX ix_order_items_order_id ON order_items (order_id);

COMMIT;
