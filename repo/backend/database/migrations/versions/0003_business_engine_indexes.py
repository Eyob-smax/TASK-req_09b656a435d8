"""Business engine composite indexes for query-critical paths

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-19 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # orders — row-level queries by candidate and auto-cancel worker
    op.create_index(
        "ix_orders_status_candidate",
        "orders",
        ["status", "candidate_id"],
    )
    op.create_index(
        "ix_orders_auto_cancel_at_status",
        "orders",
        ["auto_cancel_at", "status"],
    )

    # bargaining_threads — expiry worker
    op.create_index(
        "ix_bt_status_expires",
        "bargaining_threads",
        ["status", "window_expires_at"],
    )

    # payment_records — pending payment queue
    op.create_index(
        "ix_payment_records_confirmed_by",
        "payment_records",
        ["confirmed_by"],
    )

    # after_sales_requests — after-sales queue
    op.create_index(
        "ix_after_sales_status",
        "after_sales_requests",
        ["status"],
    )

    # attendance_exceptions — exception queue and stage routing
    op.create_index(
        "ix_exception_status_stage",
        "attendance_exceptions",
        ["status", "current_stage"],
    )


def downgrade() -> None:
    op.drop_index("ix_exception_status_stage", table_name="attendance_exceptions")
    op.drop_index("ix_after_sales_status", table_name="after_sales_requests")
    op.drop_index("ix_payment_records_confirmed_by", table_name="payment_records")
    op.drop_index("ix_bt_status_expires", table_name="bargaining_threads")
    op.drop_index("ix_orders_auto_cancel_at_status", table_name="orders")
    op.drop_index("ix_orders_status_candidate", table_name="orders")
