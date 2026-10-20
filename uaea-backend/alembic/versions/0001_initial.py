"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-03
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # contacts
    op.create_table(
        'contacts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('office_hours', sa.String(100), nullable=True),
    )

    # campuses
    op.create_table(
        'campuses',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('region', sa.String(100), nullable=False),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('contact_id', sa.String(36), sa.ForeignKey('contacts.id'), nullable=True),
    )

    # departments
    op.create_table(
        'departments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name_en', sa.String(255), nullable=False),
        sa.Column('name_ur', sa.String(255), nullable=True),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('region_id', sa.String(36), sa.ForeignKey('campuses.id'), nullable=True),
        sa.Column('contact_id', sa.String(36), sa.ForeignKey('contacts.id'), nullable=True),
    )

    # fee_tariffs
    op.create_table(
        'fee_tariffs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('program', sa.String(255), nullable=False),
        sa.Column('category', sa.String(255), nullable=False),
        sa.Column('amount', sa.Integer, nullable=False),
        sa.Column('effective_from', sa.Date, nullable=False),
        sa.Column('source_doc_ref', sa.String(255), nullable=True),
    )
    op.create_index('ix_fee_tariffs_program', 'fee_tariffs', ['program'])

    # services
    op.create_table(
        'services',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name_en', sa.String(255), nullable=False),
        sa.Column('name_ur', sa.String(255), nullable=True),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('document_checklist', sa.JSON, nullable=True),
        sa.Column('fee_id', sa.String(36), sa.ForeignKey('fee_tariffs.id'), nullable=True),
        sa.Column('deadline_id', sa.String(36), nullable=True),
        sa.Column('procedure_text', sa.Text, nullable=True),
        sa.Column('source_doc_ref', sa.String(255), nullable=True),
        sa.Column('last_verified_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_services_category', 'services', ['category'])

    # deadlines
    op.create_table(
        'deadlines',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('service_id', sa.String(36), sa.ForeignKey('services.id'), nullable=False),
        sa.Column('semester', sa.String(100), nullable=False),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('source_doc_ref', sa.String(255), nullable=True),
    )

    # knowledge_chunks (with pgvector)
    op.execute("""
        CREATE TABLE knowledge_chunks (
            id VARCHAR(36) PRIMARY KEY,
            source_doc_id VARCHAR(255) NOT NULL,
            text TEXT NOT NULL,
            embedding vector(384),
            section VARCHAR(500),
            last_verified_at TIMESTAMPTZ DEFAULT NOW(),
            superseded_by VARCHAR(36) REFERENCES knowledge_chunks(id)
        )
    """)
    op.create_index('ix_knowledge_chunks_source_doc_id', 'knowledge_chunks', ['source_doc_id'])

    # conversations
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(100), nullable=False),
        sa.Column('channel', sa.String(20), nullable=False, server_default='web'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('resolved', sa.Boolean, default=False, server_default='false'),
        sa.Column('escalated', sa.Boolean, default=False, server_default='false'),
    )
    op.create_index('ix_conversations_session_id', 'conversations', ['session_id'])

    # messages
    op.create_table(
        'messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('conversation_id', sa.String(36), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('text', sa.Text, nullable=True),
        sa.Column('intent', sa.String(60), nullable=True),
        sa.Column('tool_calls', sa.JSON, nullable=True),
        sa.Column('feedback', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # escalation_tickets
    op.create_table(
        'escalation_tickets',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('conversation_id', sa.String(36), sa.ForeignKey('conversations.id'), nullable=False),
        sa.Column('reason', sa.Text, nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='open'),
        sa.Column('assigned_to', sa.String(120), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_escalation_tickets_conversation_id', 'escalation_tickets', ['conversation_id'])

    # audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('actor', sa.String(120), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('table_name', sa.String(60), nullable=False),
        sa.Column('record_id', sa.String(60), nullable=True),
        sa.Column('detail', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # unanswered_queries
    op.create_table(
        'unanswered_queries',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('text', sa.Text, nullable=False),
        sa.Column('intent', sa.String(60), nullable=True),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('count', sa.Integer, default=1, server_default='1'),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('reason', sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('unanswered_queries')
    op.drop_table('audit_logs')
    op.drop_table('escalation_tickets')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.execute('DROP TABLE IF EXISTS knowledge_chunks')
    op.drop_table('deadlines')
    op.drop_table('services')
    op.drop_table('fee_tariffs')
    op.drop_table('departments')
    op.drop_table('campuses')
    op.drop_table('contacts')
    op.execute('DROP EXTENSION IF EXISTS vector')
