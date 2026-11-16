"""initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-11-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('role', sa.String(length=20), server_default='user', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. urls table
    op.create_table(
        'urls',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('short_code', sa.String(length=30), nullable=False),
        sa.Column('original_url', sa.Text(), nullable=False),
        sa.Column('custom_alias', sa.String(length=30), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_urls_short_code'), 'urls', ['short_code'], unique=True)
    op.create_index(op.f('ix_urls_user_id'), 'urls', ['user_id'], unique=False)
    op.create_index(op.f('ix_urls_custom_alias'), 'urls', ['custom_alias'], unique=False)
    op.create_index(op.f('ix_urls_status'), 'urls', ['status'], unique=False)
    op.create_index(op.f('ix_urls_expires_at'), 'urls', ['expires_at'], unique=False)
    op.create_index(op.f('ix_urls_created_at'), 'urls', ['created_at'], unique=False)

    # 3. click_events table
    op.create_table(
        'click_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('short_code', sa.String(length=30), nullable=False),
        sa.Column('clicked_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('referrer', sa.Text(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('ip_hash', sa.String(length=64), nullable=True),
        sa.Column('country', sa.String(length=10), nullable=True),
        sa.Column('device_type', sa.String(length=20), nullable=True),
        sa.Column('browser', sa.String(length=50), nullable=True),
        sa.Column('os', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_click_events_short_code'), 'click_events', ['short_code'], unique=False)
    op.create_index(op.f('ix_click_events_clicked_at'), 'click_events', ['clicked_at'], unique=False)
    op.create_index('ix_click_events_code_time', 'click_events', ['short_code', 'clicked_at'], unique=False)

    # 4. analytics_aggregates table
    op.create_table(
        'analytics_aggregates',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('short_code', sa.String(length=30), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('total_clicks', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('unique_visitors', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('desktop_clicks', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('mobile_clicks', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('tablet_clicks', sa.BigInteger(), server_default='0', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('short_code', 'date', name='uq_short_code_date')
    )
    op.create_index(op.f('ix_analytics_aggregates_short_code'), 'analytics_aggregates', ['short_code'], unique=False)
    op.create_index(op.f('ix_analytics_aggregates_date'), 'analytics_aggregates', ['date'], unique=False)
    op.create_index('ix_aggregates_code_date', 'analytics_aggregates', ['short_code', 'date'], unique=False)


def downgrade() -> None:
    op.drop_table('analytics_aggregates')
    op.drop_table('click_events')
    op.drop_table('urls')
    op.drop_table('users')
