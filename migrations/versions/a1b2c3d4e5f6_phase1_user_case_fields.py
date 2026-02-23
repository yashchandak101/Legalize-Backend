"""Phase 1: user and case fields (name, phone, avatar_url, is_active; assigned_lawyer_id, updated_at)

Revision ID: a1b2c3d4e5f6
Revises: 96c48c053d3d
Create Date: 2026-02-23

"""
from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "96c48c053d3d"
branch_labels = None
depends_on = None


def upgrade():
    # User: profile and active flag
    op.add_column("users", sa.Column("name", sa.String(120), nullable=True))
    op.add_column("users", sa.Column("phone", sa.String(30), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.String(500), nullable=True))
    op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")))

    # Case: updated_at and assigned_lawyer_id
    op.add_column("cases", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("cases", sa.Column("assigned_lawyer_id", sa.String(36), nullable=True))
    op.create_foreign_key(
        "fk_cases_assigned_lawyer_id_users",
        "cases",
        "users",
        ["assigned_lawyer_id"],
        ["id"],
    )
    op.create_index("ix_cases_assigned_lawyer_id", "cases", ["assigned_lawyer_id"], unique=False)


def downgrade():
    op.drop_index("ix_cases_assigned_lawyer_id", "cases")
    op.drop_constraint("fk_cases_assigned_lawyer_id_users", "cases", type_="foreignkey")
    op.drop_column("cases", "assigned_lawyer_id")
    op.drop_column("cases", "updated_at")
    op.drop_column("users", "is_active")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "phone")
    op.drop_column("users", "name")
