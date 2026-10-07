"""item_id_to_uuid

Mirrors Backend/migrations/001_item_id_to_uuid.sql, kept here so it has a
working downgrade — the original raw-SQL file has no rollback of its own.
Nothing references items.id via FK, so this is a self-contained conversion.

Revision ID: 3de373521bc4
Revises:
Create Date: 2026-09-25 15:32:35.746623

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3de373521bc4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """items.id: integer -> uuid, values regenerated (nothing referenced the
    old integer ids, so there's nothing to preserve)."""
    op.execute("ALTER TABLE items ALTER COLUMN id DROP DEFAULT")
    op.execute("ALTER TABLE items ALTER COLUMN id TYPE uuid USING gen_random_uuid()")
    op.execute("ALTER TABLE items ALTER COLUMN id SET DEFAULT gen_random_uuid()")


def downgrade() -> None:
    """items.id: uuid -> integer. The original integer values are gone
    (this is a genuine, one-way loss of the pre-upgrade ids) — this assigns
    fresh sequential ids via a window function, since nothing needs the old
    specific values preserved, only a valid integer PK again."""
    op.execute("ALTER TABLE items ALTER COLUMN id DROP DEFAULT")
    op.execute(
        "ALTER TABLE items ALTER COLUMN id TYPE integer "
        "USING (row_number() OVER (ORDER BY id))::integer"
    )
    op.execute("CREATE SEQUENCE IF NOT EXISTS items_id_seq OWNED BY items.id")
    op.execute("SELECT setval('items_id_seq', (SELECT max(id) FROM items))")
    op.execute("ALTER TABLE items ALTER COLUMN id SET DEFAULT nextval('items_id_seq')")
