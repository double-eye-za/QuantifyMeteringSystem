"""create separate permissions table

Revision ID: h3i4j5k6l789
Revises: g2h3i4j5k678
Create Date: 2025-11-18 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'h3i4j5k6l789'
down_revision = 'g2h3i4j5k678'
branch_labels = None
depends_on = None


def upgrade():
    # Check if table already exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'permissions' not in inspector.get_table_names():
        op.create_table('permissions',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('name', sa.String(length=120), nullable=False),
            sa.Column('description', sa.String(length=255), nullable=True),
            sa.Column('permissions', sa.JSON(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )


def downgrade():
    op.drop_table('permissions')
