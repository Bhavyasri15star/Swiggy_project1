"""add_coupons

Adds a coupons table (min_order_value rule only, for now — weekend/
first-order/item-restricted rules are a follow-up once this one's
verified end-to-end) and the two columns on orders needed to record
which coupon (if any) applied to a given order.

Revision ID: 7a1c9f2e3b4d
Revises: ef1b2e4b00d0
Create Date: 2026-10-02 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a1c9f2e3b4d'
down_revision: Union[str, Sequence[str], None] = 'ef1b2e4b00d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "coupons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.Text(), nullable=False, unique=True),
        sa.Column("discount_type", sa.Text(), nullable=False),
        sa.Column("discount_value", sa.Float(), nullable=False),
        sa.Column("min_order_value", sa.Float(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_index("ix_coupons_code", "coupons", ["code"])

    op.add_column("orders", sa.Column("applied_coupon_code", sa.Text(), nullable=True))
    op.add_column(
        "orders",
        sa.Column("discount_amount", sa.Float(), nullable=False, server_default="0"),
    )

    # Demo seed data, matching the codes already shown on the (previously
    # static) Offers page.
    coupons_table = sa.table(
        "coupons",
        sa.column("code", sa.Text),
        sa.column("discount_type", sa.Text),
        sa.column("discount_value", sa.Float),
        sa.column("min_order_value", sa.Float),
    )
    op.bulk_insert(
        coupons_table,
        [
            {"code": "FLAT50", "discount_type": "flat", "discount_value": 50, "min_order_value": 199},
            {"code": "BIGSAVER", "discount_type": "flat", "discount_value": 125, "min_order_value": 349},
        ],
    )


def downgrade() -> None:
    op.drop_column("orders", "discount_amount")
    op.drop_column("orders", "applied_coupon_code")
    op.drop_index("ix_coupons_code", table_name="coupons")
    op.drop_table("coupons")
