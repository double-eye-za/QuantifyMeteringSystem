"""create mobile invites table

Revision ID: t9u0v1w2x345
Revises: s8t9u0v1w234
Create Date: 2025-01-20

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 't9u0v1w2x345'
down_revision = 's8t9u0v1w234'
branch_labels = None
depends_on = None


def upgrade():
    """Create mobile_invites table for tracking invitations with temp passwords."""
    # Check if table already exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'mobile_invites' not in inspector.get_table_names():
        op.create_table(
            'mobile_invites',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('mobile_user_id', sa.Integer(), nullable=False),
            sa.Column('person_id', sa.Integer(), nullable=False),
            sa.Column('phone_number', sa.String(length=20), nullable=False),
            sa.Column('temporary_password', sa.String(length=50), nullable=False),
            sa.Column('estate_id', sa.Integer(), nullable=True),
            sa.Column('unit_id', sa.Integer(), nullable=True),
            sa.Column('role', sa.String(length=20), nullable=True),
            sa.Column('sms_sent', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('sms_error', sa.String(length=500), nullable=True),
            sa.Column('is_used', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('used_at', sa.DateTime(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['mobile_user_id'], ['mobile_users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['person_id'], ['persons.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['estate_id'], ['estates.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
        )

        # Add indexes for performance
        op.create_index('ix_mobile_invites_mobile_user_id', 'mobile_invites', ['mobile_user_id'])
        op.create_index('ix_mobile_invites_person_id', 'mobile_invites', ['person_id'])
        op.create_index('ix_mobile_invites_is_used', 'mobile_invites', ['is_used'])
        op.create_index('ix_mobile_invites_created_at', 'mobile_invites', ['created_at'])

        print("[OK] Created mobile_invites table")
    else:
        print("[OK] mobile_invites table already exists, skipping")


def downgrade():
    """Drop mobile_invites table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'mobile_invites' in inspector.get_table_names():
        op.drop_index('ix_mobile_invites_created_at', table_name='mobile_invites')
        op.drop_index('ix_mobile_invites_is_used', table_name='mobile_invites')
        op.drop_index('ix_mobile_invites_person_id', table_name='mobile_invites')
        op.drop_index('ix_mobile_invites_mobile_user_id', table_name='mobile_invites')
        op.drop_table('mobile_invites')
        print("[OK] Dropped mobile_invites table")
    else:
        print("[OK] mobile_invites table doesn't exist, skipping")
