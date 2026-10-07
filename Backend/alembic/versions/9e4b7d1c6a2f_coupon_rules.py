"""coupon_rules

Adds the weekend/first-order/item-restricted rules and a max_discount cap
(for percent coupons), and seeds the remaining four codes already shown
on the (previously decorative) Offers page -- TRYNEW, FREEDEL, WEEKEND20,
SWEETTOOTH -- as real, enforced coupons alongside FLAT50/BIGSAVER.

Note on FREEDEL: the backend has no separate "delivery fee" line item
today (DELIVERY_FEE is a frontend-only display constant, never sent to
or charged by /orders) -- so "free delivery" is implemented as a flat
discount equal to that constant (39) against the cart total, not as a
literal delivery-fee waiver. Close enough for this demo; a real delivery
fee would need its own column on Order.

Revision ID: 9e4b7d1c6a2f
Revises: 7a1c9f2e3b4d
Create Date: 2026-10-02 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '9e4b7d1c6a2f'
down_revision: Union[str, Sequence[str], None] = '7a1c9f2e3b4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("coupons", sa.Column("max_discount", sa.Float(), nullable=True))
    op.add_column(
        "coupons",
        sa.Column("requires_weekend", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "coupons",
        sa.Column("requires_first_order", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "coupons",
        sa.Column("restricted_item_names", postgresql.ARRAY(sa.Text()), nullable=True),
    )

    coupons_table = sa.table(
        "coupons",
        sa.column("code", sa.Text),
        sa.column("discount_type", sa.Text),
        sa.column("discount_value", sa.Float),
        sa.column("min_order_value", sa.Float),
        sa.column("max_discount", sa.Float),
        sa.column("requires_weekend", sa.Boolean),
        sa.column("requires_first_order", sa.Boolean),
        sa.column("restricted_item_names", postgresql.ARRAY(sa.Text())),
    )
    op.bulk_insert(
        coupons_table,
        [
            {
                "code": "TRYNEW", "discount_type": "percent", "discount_value": 50,
                "min_order_value": None, "max_discount": 100,
                "requires_weekend": False, "requires_first_order": True,
                "restricted_item_names": None,
            },
            {
                "code": "FREEDEL", "discount_type": "flat", "discount_value": 39,
                "min_order_value": None, "max_discount": None,
                "requires_weekend": False, "requires_first_order": False,
                "restricted_item_names": None,
            },
            {
                "code": "WEEKEND20", "discount_type": "percent", "discount_value": 20,
                "min_order_value": None, "max_discount": 150,
                "requires_weekend": True, "requires_first_order": False,
                "restricted_item_names": None,
            },
            {
                "code": "SWEETTOOTH", "discount_type": "percent", "discount_value": 30,
                "min_order_value": None, "max_discount": 60,
                "requires_weekend": False, "requires_first_order": False,
                "restricted_item_names": ["Coffee Mousse Cake", "Choco Mud Pie"],
            },
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM coupons WHERE code IN ('TRYNEW', 'FREEDEL', 'WEEKEND20', 'SWEETTOOTH')")
    op.drop_column("coupons", "restricted_item_names")
    op.drop_column("coupons", "requires_first_order")
    op.drop_column("coupons", "requires_weekend")
    op.drop_column("coupons", "max_discount")
