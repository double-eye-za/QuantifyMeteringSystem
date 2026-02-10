"""add consumption_hot_water transaction type

Revision ID: w2x3y4z5a678
Revises: v1w2x3y4z567
Create Date: 2026-02-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'w2x3y4z5a678'
down_revision = 'v1w2x3y4z567'
branch_labels = None
depends_on = None


def upgrade():
    # Drop old constraint
    op.drop_constraint('ck_transactions_type', 'transactions', type_='check')

    # Create new constraint with consumption_hot_water added
    op.create_check_constraint(
        'ck_transactions_type',
        'transactions',
        "transaction_type IN ("
        "'topup', 'topup_electricity', 'topup_water', 'topup_solar', 'topup_hot_water', "
        "'purchase_electricity', 'purchase_water', 'purchase_solar', "
        "'consumption_electricity', 'consumption_water', 'consumption_solar', 'consumption_hot_water', "
        "'deduction_electricity', 'deduction_water', 'deduction_solar', 'deduction_hot_water', "
        "'refund', 'adjustment', 'service_charge'"
        ")"
    )


def downgrade():
    # Drop new constraint
    op.drop_constraint('ck_transactions_type', 'transactions', type_='check')

    # Restore old constraint without consumption_hot_water
    op.create_check_constraint(
        'ck_transactions_type',
        'transactions',
        "transaction_type IN ("
        "'topup', 'topup_electricity', 'topup_water', 'topup_solar', 'topup_hot_water', "
        "'purchase_electricity', 'purchase_water', 'purchase_solar', "
        "'consumption_electricity', 'consumption_water', 'consumption_solar', "
        "'deduction_electricity', 'deduction_water', 'deduction_solar', 'deduction_hot_water', "
        "'refund', 'adjustment', 'service_charge'"
        ")"
    )
