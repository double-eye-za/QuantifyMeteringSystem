"""add status to residents

Revision ID: j5k6l7m8n901
Revises: i4j5k6l7m890
Create Date: 2025-11-18 10:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'j5k6l7m8n901'
down_revision = 'i4j5k6l7m890'
branch_labels = None
depends_on = None


def upgrade():
    # Check if column already exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('residents')]

    if 'status' not in columns:
        op.add_column('residents', sa.Column('status', sa.String(length=20),
                                             nullable=True, server_default='active'))


def downgrade():
    op.drop_column('residents', 'status')
