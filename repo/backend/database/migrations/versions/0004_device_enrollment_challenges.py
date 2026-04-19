"""Device enrollment challenge table (DB-persisted bootstrap nonces)

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-19 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "device_enrollment_challenges",
        sa.Column("challenge_id", sa.String(length=64), primary_key=True),
        sa.Column("nonce", sa.String(length=128), nullable=False),
        sa.Column("device_fingerprint", sa.String(length=128), nullable=False),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("nonce", name="uq_enroll_challenge_nonce"),
    )
    op.create_index(
        "ix_enroll_challenge_expires_at",
        "device_enrollment_challenges",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_enroll_challenge_expires_at",
        table_name="device_enrollment_challenges",
    )
    op.drop_table("device_enrollment_challenges")
