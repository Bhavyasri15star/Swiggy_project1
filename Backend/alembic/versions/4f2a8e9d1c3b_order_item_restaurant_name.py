"""order_item_restaurant_name

Snapshots which restaurant each order line came from, same reasoning as
item_name/price already being snapshots rather than live FKs. NULL on
existing rows (no way to know retroactively without the original cart
state) -- only ever NULL for orders placed before this migration.

Revision ID: 4f2a8e9d1c3b
Revises: 9e4b7d1c6a2f
Create Date: 2026-10-02 19:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f2a8e9d1c3b'
down_revision: Union[str, Sequence[str], None] = '9e4b7d1c6a2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("order_items", sa.Column("restaurant_name", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("order_items", "restaurant_name")
