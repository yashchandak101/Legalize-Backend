"""Phase 4: payments and notifications

Revision ID: d4e5f6g7h8i
Revises: c3d4e5f6g7h8
Create Date: 2026-02-23

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d4e5f6g7h8i"
down_revision = "c3d4e5f6g7h8"
branch_labels = None
depends_on = None


def upgrade():
    # Create payments table
    op.create_table(
        "payments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("case_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="usd"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("stripe_payment_intent_id", sa.String(255), nullable=True, unique=True),
        sa.Column("stripe_client_secret", sa.String(255), nullable=True),
        sa.Column("stripe_charge_id", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("payment_metadata", sa.JSON(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("refunded_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ),
    )
    op.create_index("ix_payments_case_id", "payments", ["case_id"], unique=False)
    op.create_index("ix_payments_user_id", "payments", ["user_id"], unique=False)
    op.create_index("ix_payments_stripe_payment_intent_id", "payments", ["stripe_payment_intent_id"], unique=True)

    # Create notifications table
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("kind", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"], unique=False)
    op.create_index("ix_notifications_read_at", "notifications", ["read_at"], unique=False)
    op.create_index("ix_notifications_kind", "notifications", ["kind"], unique=False)


def downgrade():
    # Drop notifications table
    op.drop_index("ix_notifications_kind", "notifications")
    op.drop_index("ix_notifications_read_at", "notifications")
    op.drop_index("ix_notifications_user_id", "notifications")
    op.drop_table("notifications")

    # Drop payments table
    op.drop_index("ix_payments_stripe_payment_intent_id", "payments")
    op.drop_index("ix_payments_user_id", "payments")
    op.drop_index("ix_payments_case_id", "payments")
    op.drop_table("payments")
