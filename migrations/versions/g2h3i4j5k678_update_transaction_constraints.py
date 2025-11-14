"""update transaction constraints for wallet topup

Revision ID: g2h3i4j5k678
Revises: f1a2b3c4d5e6
Create Date: 2025-11-14 12:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'g2h3i4j5k678'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    # Drop old constraints
    op.drop_constraint('ck_transactions_type', 'transactions', type_='check')
    op.drop_constraint('ck_transactions_payment_method', 'transactions', type_='check')

    # Create new constraints with updated values
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

    op.create_check_constraint(
        'ck_transactions_payment_method',
        'transactions',
        "payment_method IS NULL OR payment_method IN ("
        "'eft', 'card', 'instant_eft', 'cash', 'system', 'adjustment', 'manual_admin'"
        ")"
    )


def downgrade():
    # Drop new constraints
    op.drop_constraint('ck_transactions_type', 'transactions', type_='check')
    op.drop_constraint('ck_transactions_payment_method', 'transactions', type_='check')

    # Restore old constraints
    op.create_check_constraint(
        'ck_transactions_type',
        'transactions',
        "transaction_type IN ("
        "'topup', 'purchase_electricity', 'purchase_water', 'purchase_solar', "
        "'consumption_electricity', 'consumption_water', 'consumption_solar', "
        "'refund', 'adjustment', 'service_charge'"
        ")"
    )

    op.create_check_constraint(
        'ck_transactions_payment_method',
        'transactions',
        "payment_method IS NULL OR payment_method IN ("
        "'eft', 'card', 'instant_eft', 'cash', 'system', 'adjustment'"
        ")"
    )
