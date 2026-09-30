"""Initial schema — all 8 tables

Revision ID: 0001
Revises:
Create Date: 2026-09-30
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("member_id", sa.String(4), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("totp_secret_encrypted", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("member_id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_students_member_id", "students", ["member_id"])

    op.create_table(
        "challenges",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("range_challenge_id", sa.String(255), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("range_challenge_id"),
    )
    op.create_index("ix_challenges_range_challenge_id", "challenges", ["range_challenge_id"])

    op.create_table(
        "devices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_name", sa.String(255), nullable=False),
        sa.Column("api_key_hash", sa.String(64), nullable=False),
        sa.Column("firmware_version", sa.String(50), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("device_name"),
    )

    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("cost_credits", sa.Integer(), nullable=False),
        sa.Column("stock_qty", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "unlock_eligibilities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("challenge_id", sa.Integer(), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.ForeignKeyConstraint(["challenge_id"], ["challenges.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_eligibility_student_consumed",
        "unlock_eligibilities",
        ["student_id", "consumed_at"],
    )

    op.create_table(
        "unlock_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=True),
        sa.Column("member_id_raw", sa.String(10), nullable=False),
        sa.Column(
            "result",
            sa.Enum(
                "granted",
                "invalid_format",
                "unknown_member",
                "invalid_totp",
                "no_eligibility",
                "member_inactive",
                "forced_open",
                name="unlockresult",
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "redemptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("credits_spent", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "credit_ledger",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(255), nullable=False),
        sa.Column("challenge_id", sa.Integer(), nullable=True),
        sa.Column("redemption_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.ForeignKeyConstraint(["challenge_id"], ["challenges.id"]),
        sa.ForeignKeyConstraint(["redemption_id"], ["redemptions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("credit_ledger")
    op.drop_table("redemptions")
    op.drop_table("unlock_events")
    op.drop_index("ix_eligibility_student_consumed", "unlock_eligibilities")
    op.drop_table("unlock_eligibilities")
    op.drop_table("items")
    op.drop_table("devices")
    op.drop_index("ix_challenges_range_challenge_id", "challenges")
    op.drop_table("challenges")
    op.drop_index("ix_students_member_id", "students")
    op.drop_table("students")
    op.execute("DROP TYPE IF EXISTS unlockresult")
