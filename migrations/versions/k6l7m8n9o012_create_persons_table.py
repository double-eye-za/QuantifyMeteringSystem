"""create persons table

Revision ID: k6l7m8n9o012
Revises: j5k6l7m8n901
Create Date: 2025-11-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'k6l7m8n9o012'
down_revision = 'j5k6l7m8n901'
branch_labels = None
depends_on = None


def upgrade():
    """
    Create the persons table - core identity for all app users (owners, tenants).
    This table will replace the residents table with support for multiple roles.
    """
    op.create_table(
        'persons',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('alternate_phone', sa.String(length=20), nullable=True),
        sa.Column('id_number', sa.String(length=20), nullable=True),
        sa.Column('emergency_contact_name', sa.String(length=200), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(length=20), nullable=True),
        sa.Column('app_user_id', sa.String(length=36), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('profile_photo_url', sa.String(length=512), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_persons_email'),
        sa.UniqueConstraint('id_number', name='uq_persons_id_number'),
        sa.UniqueConstraint('app_user_id', name='uq_persons_app_user_id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_persons_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_persons_updated_by'),
    )

    # Create indexes for performance
    op.create_index('ix_persons_email', 'persons', ['email'])
    op.create_index('ix_persons_id_number', 'persons', ['id_number'])
    op.create_index('ix_persons_app_user_id', 'persons', ['app_user_id'])
    op.create_index('ix_persons_is_active', 'persons', ['is_active'])


def downgrade():
    """Remove persons table and indexes"""
    op.drop_index('ix_persons_is_active', 'persons')
    op.drop_index('ix_persons_app_user_id', 'persons')
    op.drop_index('ix_persons_id_number', 'persons')
    op.drop_index('ix_persons_email', 'persons')
    op.drop_table('persons')
