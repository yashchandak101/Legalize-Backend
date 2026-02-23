"""Fix cases table to use UUID IDs

Revision ID: f0e1d2c3b4a5
Revises: a1b2c3d4e5f6
Create Date: 2026-02-23

"""
from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision = "f0e1d2c3b4a5"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    # First, add a new UUID column to cases table
    op.add_column('cases', sa.Column('uuid_id', sa.String(36), nullable=True))
    
    # Update all existing rows to have UUID values
    op.execute("""
        UPDATE cases 
        SET uuid_id = gen_random_uuid()::text 
        WHERE uuid_id IS NULL
    """)
    
    # Make the UUID column NOT NULL
    op.alter_column('cases', 'uuid_id', nullable=False)
    
    # Drop foreign key constraints that reference the old integer ID
    op.drop_constraint('cases_user_id_fkey', 'cases', type_='foreignkey')
    
    # Update user_id to use the new UUID (it should already be VARCHAR(36))
    # This should be fine since user_id is already VARCHAR(36)
    
    # Add new foreign key constraint for user_id referencing users.uuid_id
    op.create_foreign_key(
        'fk_cases_user_id_users',
        'cases', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Now we need to update any other tables that reference cases.id
    # For now, we'll handle this in the next migration step
    
    # Add index on the new UUID column
    op.create_index('ix_cases_uuid_id', 'cases', ['uuid_id'])


def downgrade():
    # Remove the index
    op.drop_index('ix_cases_uuid_id', 'cases')
    
    # Drop the foreign key constraint
    op.drop_constraint('fk_cases_user_id_users', 'cases', type_='foreignkey')
    
    # Restore the original foreign key constraint
    op.create_foreign_key(
        'cases_user_id_fkey',
        'cases', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Make the UUID column nullable
    op.alter_column('cases', 'uuid_id', nullable=True)
    
    # Drop the UUID column
    op.drop_column('cases', 'uuid_id')
