"""Phase 3: case comments and documents

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-02-23

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c3d4e5f6g7h8"
down_revision = "b2c3d4e5f6g7"
branch_labels = None
depends_on = None


def upgrade():
    # Create case_comments table
    op.create_table(
        "case_comments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("case_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_internal", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ),
    )
    op.create_index("ix_case_comments_case_id", "case_comments", ["case_id"], unique=False)
    op.create_index("ix_case_comments_user_id", "case_comments", ["user_id"], unique=False)

    # Create case_documents table
    op.create_table(
        "case_documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("case_id", sa.String(36), nullable=False),
        sa.Column("uploaded_by", sa.String(36), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(500), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ),
    )
    op.create_index("ix_case_documents_case_id", "case_documents", ["case_id"], unique=False)
    op.create_index("ix_case_documents_uploaded_by", "case_documents", ["uploaded_by"], unique=False)
    op.create_index("ix_case_documents_is_deleted", "case_documents", ["is_deleted"], unique=False)


def downgrade():
    # Drop case_documents table
    op.drop_index("ix_case_documents_is_deleted", "case_documents")
    op.drop_index("ix_case_documents_uploaded_by", "case_documents")
    op.drop_index("ix_case_documents_case_id", "case_documents")
    op.drop_table("case_documents")

    # Drop case_comments table
    op.drop_index("ix_case_comments_user_id", "case_comments")
    op.drop_index("ix_case_comments_case_id", "case_comments")
    op.drop_table("case_comments")
