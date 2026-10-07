"""restaurant_id_to_uuid

Mirrors Backend/migrations/002_restaurant_id_to_uuid.sql. Unlike 001
(items.id, nothing referenced it), items.restaurant_id is a real FK, so
both upgrade and downgrade preserve the actual relationship by joining on
the OLD id before it's dropped — never assigning new values independently
on each side.

Revision ID: 3584d7a4178a
Revises: 3de373521bc4
Create Date: 2026-09-25 15:32:36.734815

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3584d7a4178a'
down_revision: Union[str, Sequence[str], None] = '3de373521bc4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """restaurants.id + items.restaurant_id: integer -> uuid."""
    op.execute("ALTER TABLE restaurants ADD COLUMN new_id uuid NOT NULL DEFAULT gen_random_uuid()")

    op.execute("ALTER TABLE items ADD COLUMN new_restaurant_id uuid")
    op.execute(
        "UPDATE items SET new_restaurant_id = r.new_id "
        "FROM restaurants r WHERE items.restaurant_id = r.id"
    )
    op.execute("ALTER TABLE items ALTER COLUMN new_restaurant_id SET NOT NULL")

    # FK depends on the old pkey's index — has to drop first.
    op.execute("ALTER TABLE items DROP CONSTRAINT items_restaurant_id_fkey")

    op.execute("ALTER TABLE restaurants DROP CONSTRAINT restaurants_pkey")
    op.execute("ALTER TABLE restaurants DROP COLUMN id")
    op.execute("ALTER TABLE restaurants RENAME COLUMN new_id TO id")
    op.execute("ALTER TABLE restaurants ADD PRIMARY KEY (id)")
    op.execute("ALTER TABLE restaurants ALTER COLUMN id SET DEFAULT gen_random_uuid()")

    op.execute("ALTER TABLE items DROP COLUMN restaurant_id")
    op.execute("ALTER TABLE items RENAME COLUMN new_restaurant_id TO restaurant_id")
    op.execute(
        "ALTER TABLE items ADD CONSTRAINT items_restaurant_id_fkey "
        "FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)"
    )


def downgrade() -> None:
    """restaurants.id + items.restaurant_id: uuid -> integer. Same
    join-before-drop approach as upgrade(), just assigning fresh sequential
    integers instead of random uuids — the relationship is still preserved
    exactly, only the id values themselves are (necessarily) new."""
    op.execute("ALTER TABLE restaurants ADD COLUMN new_id integer")
    op.execute(
        "UPDATE restaurants SET new_id = sub.rn FROM ("
        "  SELECT id, row_number() OVER (ORDER BY id) AS rn FROM restaurants"
        ") sub WHERE restaurants.id = sub.id"
    )
    op.execute("ALTER TABLE restaurants ALTER COLUMN new_id SET NOT NULL")

    op.execute("ALTER TABLE items ADD COLUMN new_restaurant_id integer")
    op.execute(
        "UPDATE items SET new_restaurant_id = r.new_id "
        "FROM restaurants r WHERE items.restaurant_id = r.id"
    )
    op.execute("ALTER TABLE items ALTER COLUMN new_restaurant_id SET NOT NULL")

    op.execute("ALTER TABLE items DROP CONSTRAINT items_restaurant_id_fkey")

    op.execute("ALTER TABLE restaurants DROP CONSTRAINT restaurants_pkey")
    op.execute("ALTER TABLE restaurants DROP COLUMN id")
    op.execute("ALTER TABLE restaurants RENAME COLUMN new_id TO id")
    op.execute("ALTER TABLE restaurants ADD PRIMARY KEY (id)")
    op.execute("CREATE SEQUENCE IF NOT EXISTS restaurants_id_seq OWNED BY restaurants.id")
    op.execute("SELECT setval('restaurants_id_seq', (SELECT max(id) FROM restaurants))")
    op.execute("ALTER TABLE restaurants ALTER COLUMN id SET DEFAULT nextval('restaurants_id_seq')")

    op.execute("ALTER TABLE items DROP COLUMN restaurant_id")
    op.execute("ALTER TABLE items RENAME COLUMN new_restaurant_id TO restaurant_id")
    op.execute(
        "ALTER TABLE items ADD CONSTRAINT items_restaurant_id_fkey "
        "FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)"
    )
