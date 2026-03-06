"""create meter_photos table for storing meter photo metadata

Revision ID: d8e9f0g1h234
Revises: c7d8e9f0g123
Create Date: 2026-03-06 14:00:00.000000

Adds a meter_photos table to store metadata about uploaded meter photos.
Photos are stored on disk at app/static/uploads/meters/{meter_id}/.
FK to meters with CASCADE delete — photos are removed when a meter is deleted.
"""
from alembic import op
import sqlalchemy as sa

revision = 'd8e9f0g1h234'
down_revision = 'c7d8e9f0g123'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'meter_photos',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('meter_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(50), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['meter_id'], ['meters.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_meter_photos_meter_id', 'meter_photos', ['meter_id'])


def downgrade():
    op.drop_index('ix_meter_photos_meter_id', 'meter_photos')
    op.drop_table('meter_photos')
