"""create_orders

Mirrors Backend/migrations/003_create_orders.sql. orders.user_id is TEXT,
not a native FK-enforced column at the SQLAlchemy level, because it
references auth.users(id) — owned by AuthService/Prisma, not a table
SQLAlchemy has mapped here (see core/models.py's comment on Order.user_id
for why a real FK() there breaks flush-time table sorting). The database-
level REFERENCES constraint below is what actually enforces it.

Revision ID: 2884240ad723
Revises: 3584d7a4178a
Create Date: 2026-09-25 15:32:37.716077

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2884240ad723'
down_revision: Union[str, Sequence[str], None] = '3584d7a4178a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE orders (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id TEXT NOT NULL REFERENCES auth.users(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            total_amount DOUBLE PRECISION NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX ix_orders_user_id ON orders (user_id)")
    op.execute("CREATE INDEX ix_orders_created_at ON orders (created_at)")

    op.execute(
        """
        CREATE TABLE order_items (
            id SERIAL PRIMARY KEY,
            order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            item_id UUID REFERENCES items(id),
            item_name TEXT NOT NULL,
            price DOUBLE PRECISION NOT NULL,
            quantity INTEGER NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX ix_order_items_order_id ON order_items (order_id)")


def downgrade() -> None:
    """Drops both tables — this is a genuine, real data loss if any orders
    have been placed since this was applied, not just a schema revert.
    order_items is dropped first since it FKs into orders."""
    op.execute("DROP TABLE IF EXISTS order_items")
    op.execute("DROP TABLE IF EXISTS orders")
