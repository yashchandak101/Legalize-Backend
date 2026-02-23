"""Phase 5: AI suggestions and background workers

Revision ID: e5f6g7h8i9j
Revises: d4e5f6g7h8i
Create Date: 2026-02-23

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e5f6g7h8i9j"
down_revision = "d4e5f6g7h8i"
branch_labels = None
depends_on = None


def upgrade():
    # Create case_ai_suggestions table
    op.create_table(
        "case_ai_suggestions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("case_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("suggestion_type", sa.String(50), nullable=False, server_default="case_suggestions"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("provider", sa.String(50), nullable=True),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("suggestions", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("request_data", sa.JSON(), nullable=True),
        sa.Column("processing_time_ms", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ),
    )
    op.create_index("ix_case_ai_suggestions_case_id", "case_ai_suggestions", ["case_id"], unique=False)
    op.create_index("ix_case_ai_suggestions_user_id", "case_ai_suggestions", ["user_id"], unique=False)
    op.create_index("ix_case_ai_suggestions_type", "case_ai_suggestions", ["suggestion_type"], unique=False)
    op.create_index("ix_case_ai_suggestions_status", "case_ai_suggestions", ["status"], unique=False)
    op.create_index("ix_case_ai_suggestions_created_at", "case_ai_suggestions", ["created_at"], unique=False)


def downgrade():
    # Drop case_ai_suggestions table
    op.drop_index("ix_case_ai_suggestions_created_at", "case_ai_suggestions")
    op.drop_index("ix_case_ai_suggestions_status", "case_ai_suggestions")
    op.drop_index("ix_case_ai_suggestions_type", "case_ai_suggestions")
    op.drop_index("ix_case_ai_suggestions_user_id", "case_ai_suggestions")
    op.drop_index("ix_case_ai_suggestions_case_id", "case_ai_suggestions")
    op.drop_table("case_ai_suggestions")
