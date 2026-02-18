"""Add hot_water_meter_id to units table and update meter_type constraint

Revision ID: b4c8e7f9a123
Revises: a315b31ddf24
Create Date: 2025-01-21 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b4c8e7f9a123"
down_revision = "a315b31ddf24"
branch_labels = None
depends_on = None


def upgrade():
    # Add hot_water_meter_id column to units table
    with op.batch_alter_table("units", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("hot_water_meter_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_units_hot_water_meter_id", "meters", ["hot_water_meter_id"], ["id"]
        )

    # Add hot_water_balance column to wallets table
    with op.batch_alter_table("wallets", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "hot_water_balance",
                sa.Numeric(12, 2),
                nullable=False,
                server_default="0.00",
            )
        )

    # Update meter_type constraint to include hot_water
    with op.batch_alter_table("meters", schema=None) as batch_op:
        batch_op.drop_constraint("ck_meters_type", type_="check")
        batch_op.create_check_constraint(
            "ck_meters_type",
            "meter_type IN ('electricity','water','solar','hot_water','bulk_electricity','bulk_water')",
        )


def downgrade():
    # Revert meter_type constraint
    with op.batch_alter_table("meters", schema=None) as batch_op:
        batch_op.drop_constraint("ck_meters_type", type_="check")
        batch_op.create_check_constraint(
            "ck_meters_type",
            "meter_type IN ('electricity','water','solar','bulk_electricity','bulk_water')",
        )

    # Remove hot_water_balance column from wallets table
    with op.batch_alter_table("wallets", schema=None) as batch_op:
        batch_op.drop_column("hot_water_balance")

    # Remove hot_water_meter_id column from units table
    with op.batch_alter_table("units", schema=None) as batch_op:
        batch_op.drop_constraint("fk_units_hot_water_meter_id", type_="foreignkey")
        batch_op.drop_column("hot_water_meter_id")
