"""Initial database schema setup.

Revision ID: 000_initial
Revises: 
Create Date: 2024-10-31 05:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '000_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial tables."""
    
    # Create enums
    op.execute('CREATE TYPE style_preset AS ENUM (\'formal\', \'friendly\', \'brief\')')
    op.execute('CREATE TYPE provider AS ENUM (\'gmail\', \'demo\', \'outlook\')')
    op.execute('CREATE TYPE mailbox_status AS ENUM (\'connected\', \'needs_reconnect\', \'revoked\', \'disconnected\')')
    op.execute('CREATE TYPE sync_status AS ENUM (\'idle\', \'backfilling\', \'syncing\', \'error\')')
    op.execute('CREATE TYPE job_status AS ENUM (\'queued\', \'running\', \'succeeded\', \'failed\', \'cancelled\', \'dead\')')

    # users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.func.gen_random_uuid(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('google_sub', sa.String(255), nullable=False),
        sa.Column('is_demo', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('style_preset', postgresql.ENUM('formal', 'friendly', 'brief', name='style_preset'), nullable=False, server_default='formal'),
        sa.Column('signature', sa.Text(), nullable=True),
        sa.Column('label_sync_enabled', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_users_email'),
        sa.UniqueConstraint('google_sub', name='uq_users_google_sub'),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_google_sub', 'users', ['google_sub'])

    # sessions table
    op.create_table(
        'sessions',
        sa.Column('id', sa.String(256), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('ip_hash', sa.String(64), nullable=True),
        sa.Column('user_agent', sa.String(512), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_sessions_user_id', 'sessions', ['user_id'])

    # mailboxes table
    op.create_table(
        'mailboxes',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.func.gen_random_uuid(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', postgresql.ENUM('gmail', 'demo', 'outlook', name='provider'), nullable=False, server_default='gmail'),
        sa.Column('email_address', sa.String(255), nullable=False),
        sa.Column('encrypted_refresh_token', sa.LargeBinary(), nullable=True),
        sa.Column('key_version', sa.Integer(), nullable=True),
        sa.Column('scopes', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('history_id', sa.String(64), nullable=True),
        sa.Column('status', postgresql.ENUM('connected', 'needs_reconnect', 'revoked', 'disconnected', name='mailbox_status'), nullable=False, server_default='connected'),
        sa.Column('sync_status', postgresql.ENUM('idle', 'backfilling', 'syncing', 'error', name='sync_status'), nullable=False, server_default='idle'),
        sa.Column('backfill_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'provider', name='uq_mailbox_user_provider'),
    )
    op.create_index('ix_mailboxes_user_id', 'mailboxes', ['user_id'])

    # categories table
    op.create_table(
        'categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.func.gen_random_uuid(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('examples', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('color', sa.String(7), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('gmail_label_id', sa.String(255), nullable=True),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'slug', name='uq_category_user_slug'),
    )
    op.create_index('ix_categories_user_id', 'categories', ['user_id'])

    # jobs table
    op.create_table(
        'jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.func.gen_random_uuid(), nullable=False),
        sa.Column('type', sa.String(64), nullable=False),
        sa.Column('payload', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('status', postgresql.ENUM('queued', 'running', 'succeeded', 'failed', 'cancelled', 'dead', name='job_status'), nullable=False, server_default='queued'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('run_after', sa.DateTime(timezone=True), nullable=True),
        sa.Column('locked_by', sa.String(128), nullable=True),
        sa.Column('locked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('heartbeat_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dedupe_key', sa.String(256), nullable=True),
        sa.Column('cancel_requested', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('mailbox_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['mailbox_id'], ['mailboxes.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dedupe_key', name='uq_jobs_dedupe_key'),
    )
    op.create_index('ix_jobs_type', 'jobs', ['type'])
    op.create_index('ix_jobs_status', 'jobs', ['status'])
    op.create_index('ix_jobs_user_id', 'jobs', ['user_id'])
    op.create_index('ix_jobs_mailbox_id', 'jobs', ['mailbox_id'])
    op.create_index('ix_jobs_created_at', 'jobs', ['created_at'])

    # job_events table
    op.create_table(
        'job_events',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(64), nullable=False),
        sa.Column('data', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_job_events_job_id', 'job_events', ['job_id'])
    op.create_index('ix_job_events_user_id', 'job_events', ['user_id'])
    op.create_index('ix_job_events_created_at', 'job_events', ['created_at'])

    # audit_log table
    op.create_table(
        'audit_log',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(64), nullable=False),
        sa.Column('entity_type', sa.String(64), nullable=True),
        sa.Column('entity_id', sa.String(255), nullable=True),
        sa.Column('payload', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('prev_hash', sa.String(64), nullable=True),
        sa.Column('row_hash', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_log_user_id', 'audit_log', ['user_id'])
    op.create_index('ix_audit_log_event_type', 'audit_log', ['event_type'])
    op.create_index('ix_audit_log_created_at', 'audit_log', ['created_at'])

    # system_flags table
    op.create_table(
        'system_flags',
        sa.Column('key', sa.String(255), nullable=False),
        sa.Column('value', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('updated_by', sa.String(255), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('key'),
    )
    op.create_index('ix_system_flags_updated_at', 'system_flags', ['updated_at'])

    # Create audit log immutability trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION audit_log_immutable()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log is immutable: no updates or deletes allowed';
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER audit_log_no_update
        BEFORE UPDATE ON audit_log
        FOR EACH ROW
        EXECUTE PROCEDURE audit_log_immutable();
    """)

    op.execute("""
        CREATE TRIGGER audit_log_no_delete
        BEFORE DELETE ON audit_log
        FOR EACH ROW
        EXECUTE PROCEDURE audit_log_immutable();
    """)


def downgrade() -> None:
    """Drop all tables and enums."""
    
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS audit_log_no_delete ON audit_log;")
    op.execute("DROP TRIGGER IF EXISTS audit_log_no_update ON audit_log;")
    op.execute("DROP FUNCTION IF EXISTS audit_log_immutable();")

    # Drop tables
    op.drop_table('system_flags')
    op.drop_table('audit_log')
    op.drop_table('job_events')
    op.drop_table('jobs')
    op.drop_table('categories')
    op.drop_table('mailboxes')
    op.drop_table('sessions')
    op.drop_table('users')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS job_status;")
    op.execute("DROP TYPE IF EXISTS sync_status;")
    op.execute("DROP TYPE IF EXISTS mailbox_status;")
    op.execute("DROP TYPE IF EXISTS provider;")
    op.execute("DROP TYPE IF EXISTS style_preset;")
