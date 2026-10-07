"""add_order_status

Mirrors Backend/migrations/004_add_order_status.sql. The simplest and
safest revision in this chain — a plain additive column with a default,
so its downgrade is fully lossless as long as nothing has since been
cancelled/delivered (those values are genuinely lost on downgrade, same
as any column drop would be).

Revision ID: ef1b2e4b00d0
Revises: 2884240ad723
Create Date: 2026-09-25 15:32:38.692220

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ef1b2e4b00d0'
down_revision: Union[str, Sequence[str], None] = '2884240ad723'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column("status", sa.Text(), nullable=False, server_default="placed"),
    )


def downgrade() -> None:
    op.drop_column("orders", "status")
