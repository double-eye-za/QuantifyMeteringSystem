"""create mobile users table

Revision ID: p5q6r7s8t901
Revises: o0p1q2r3s456
Create Date: 2025-01-19

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'p5q6r7s8t901'
down_revision = 'o0p1q2r3s456'
branch_labels = None
depends_on = None


def upgrade():
    """Create mobile_users table for mobile app authentication."""
    # Check if table already exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'mobile_users' not in inspector.get_table_names():
        op.create_table(
            'mobile_users',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('person_id', sa.Integer(), nullable=False),
            sa.Column('phone_number', sa.String(length=20), nullable=False),
            sa.Column('password_hash', sa.String(length=255), nullable=False),
            sa.Column('temporary_password_hash', sa.String(length=255), nullable=True),
            sa.Column('password_must_change', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('last_login', sa.DateTime(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['person_id'], ['persons.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('person_id', name='uq_mobile_users_person_id'),
            sa.UniqueConstraint('phone_number', name='uq_mobile_users_phone_number')
        )

        # Add indexes for performance
        op.create_index('ix_mobile_users_phone_number', 'mobile_users', ['phone_number'])
        op.create_index('ix_mobile_users_person_id', 'mobile_users', ['person_id'])

        print("[OK] Created mobile_users table")
    else:
        print("[OK] mobile_users table already exists, skipping")


def downgrade():
    """Drop mobile_users table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'mobile_users' in inspector.get_table_names():
        op.drop_index('ix_mobile_users_person_id', table_name='mobile_users')
        op.drop_index('ix_mobile_users_phone_number', table_name='mobile_users')
        op.drop_table('mobile_users')
        print("[OK] Dropped mobile_users table")
    else:
        print("[OK] mobile_users table doesn't exist, skipping")
