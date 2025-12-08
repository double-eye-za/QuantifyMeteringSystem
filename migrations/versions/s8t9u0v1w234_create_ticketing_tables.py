"""create ticketing tables

Revision ID: s8t9u0v1w234
Revises: r7s8t9u0v123
Create Date: 2025-12-04 10:00:00.000000

Description:
    Create the ticketing system tables:
    - ticket_categories: Dynamic categories for support tickets
    - tickets: Main support ticket table
    - ticket_messages: Replies/messages within tickets

    Tickets are created by persons (mobile app users) and managed by users (staff).
    Categories are stored in a separate table for dynamic management.

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 's8t9u0v1w234'
down_revision = 'r7s8t9u0v123'
branch_labels = None
depends_on = None


def upgrade():
    """
    Create the ticketing system tables.
    """
    # Create ticket_categories table
    op.create_table(
        'ticket_categories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('display_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_ticket_categories_name'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_ticket_categories_created_by'),
    )

    # Create tickets table
    op.create_table(
        'tickets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('ticket_number', sa.String(length=20), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='open'),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('created_by_person_id', sa.Integer(), nullable=False),
        sa.Column('assigned_to_user_id', sa.Integer(), nullable=True),
        sa.Column('unit_id', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ticket_number', name='uq_tickets_ticket_number'),
        sa.ForeignKeyConstraint(['category_id'], ['ticket_categories.id'], name='fk_tickets_category_id'),
        sa.ForeignKeyConstraint(['created_by_person_id'], ['persons.id'], name='fk_tickets_created_by_person_id'),
        sa.ForeignKeyConstraint(['assigned_to_user_id'], ['users.id'], name='fk_tickets_assigned_to_user_id'),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id'], name='fk_tickets_unit_id'),
        sa.CheckConstraint(
            "status IN ('open','in_progress','pending','resolved','closed')",
            name='ck_tickets_status'
        ),
        sa.CheckConstraint(
            "priority IN ('low','medium','high','urgent')",
            name='ck_tickets_priority'
        ),
    )

    # Create ticket_messages table
    op.create_table(
        'ticket_messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('ticket_id', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('sender_type', sa.String(length=20), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('is_internal', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], name='fk_ticket_messages_ticket_id', ondelete='CASCADE'),
        sa.CheckConstraint(
            "sender_type IN ('staff','customer')",
            name='ck_ticket_messages_sender_type'
        ),
    )

    # Create indexes for performance
    op.create_index('ix_tickets_ticket_number', 'tickets', ['ticket_number'])
    op.create_index('ix_tickets_status', 'tickets', ['status'])
    op.create_index('ix_tickets_priority', 'tickets', ['priority'])
    op.create_index('ix_tickets_created_by_person_id', 'tickets', ['created_by_person_id'])
    op.create_index('ix_tickets_assigned_to_user_id', 'tickets', ['assigned_to_user_id'])
    op.create_index('ix_tickets_created_at', 'tickets', ['created_at'])
    op.create_index('ix_ticket_messages_ticket_id', 'ticket_messages', ['ticket_id'])
    op.create_index('ix_ticket_messages_created_at', 'ticket_messages', ['created_at'])

    # Insert default categories
    op.execute("""
        INSERT INTO ticket_categories (name, description, icon, color, is_active, display_order)
        VALUES
            ('Billing & Payments', 'Questions about billing, payments, or account balance', 'fa-credit-card', 'blue', true, 1),
            ('Meter Issues', 'Problems with meter readings or meter functionality', 'fa-tachometer-alt', 'red', true, 2),
            ('Water Supply', 'Issues related to water supply or quality', 'fa-water', 'cyan', true, 3),
            ('Electricity Supply', 'Issues related to electricity supply', 'fa-bolt', 'yellow', true, 4),
            ('App Technical Support', 'Help with the mobile app or website', 'fa-mobile-alt', 'purple', true, 5),
            ('General Enquiry', 'General questions or feedback', 'fa-question-circle', 'gray', true, 6)
    """)


def downgrade():
    """Remove ticketing tables and indexes"""
    # Drop indexes
    op.drop_index('ix_ticket_messages_created_at', 'ticket_messages')
    op.drop_index('ix_ticket_messages_ticket_id', 'ticket_messages')
    op.drop_index('ix_tickets_created_at', 'tickets')
    op.drop_index('ix_tickets_assigned_to_user_id', 'tickets')
    op.drop_index('ix_tickets_created_by_person_id', 'tickets')
    op.drop_index('ix_tickets_priority', 'tickets')
    op.drop_index('ix_tickets_status', 'tickets')
    op.drop_index('ix_tickets_ticket_number', 'tickets')

    # Drop tables in reverse order due to foreign keys
    op.drop_table('ticket_messages')
    op.drop_table('tickets')
    op.drop_table('ticket_categories')
