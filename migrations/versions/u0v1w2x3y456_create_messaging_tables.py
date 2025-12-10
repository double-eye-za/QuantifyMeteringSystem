"""create messaging tables

Revision ID: u0v1w2x3y456
Revises: t9u0v1w2x345
Create Date: 2024-12-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'u0v1w2x3y456'
down_revision = 't9u0v1w2x345'
branch_labels = None
depends_on = None


def upgrade():
    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('subject', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(20), nullable=False),
        sa.Column('sender_user_id', sa.Integer(), nullable=False),
        sa.Column('estate_id', sa.Integer(), nullable=True),
        sa.Column('recipient_person_id', sa.Integer(), nullable=True),
        sa.Column('recipient_count', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['sender_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['estate_id'], ['estates.id']),
        sa.ForeignKeyConstraint(['recipient_person_id'], ['persons.id']),
        sa.CheckConstraint(
            "message_type IN ('broadcast', 'estate', 'individual')",
            name='ck_messages_type'
        ),
    )

    # Create index on messages
    op.create_index('ix_messages_message_type', 'messages', ['message_type'])
    op.create_index('ix_messages_sent_at', 'messages', ['sent_at'])
    op.create_index('ix_messages_sender_user_id', 'messages', ['sender_user_id'])

    # Create message_recipients table
    op.create_table(
        'message_recipients',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('person_id', sa.Integer(), nullable=False),
        sa.Column('is_read', sa.Boolean(), default=False, nullable=False),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['person_id'], ['persons.id']),
        sa.UniqueConstraint('message_id', 'person_id', name='uq_message_recipient'),
    )

    # Create indexes on message_recipients
    op.create_index('ix_message_recipients_message_id', 'message_recipients', ['message_id'])
    op.create_index('ix_message_recipients_person_read', 'message_recipients', ['person_id', 'is_read'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_message_recipients_person_read', table_name='message_recipients')
    op.drop_index('ix_message_recipients_message_id', table_name='message_recipients')
    op.drop_index('ix_messages_sender_user_id', table_name='messages')
    op.drop_index('ix_messages_sent_at', table_name='messages')
    op.drop_index('ix_messages_message_type', table_name='messages')

    # Drop tables
    op.drop_table('message_recipients')
    op.drop_table('messages')
