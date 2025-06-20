"""empty message

Revision ID: fb705712f1ab
Revises:
Create Date: 2024-12-17 07:53:03.882442

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fb705712f1ab'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'ai_models',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('show_name', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'languages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('iso_code', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('iso_code'),
        sa.UniqueConstraint('name'),
    )
    op.create_table(
        'report_reasons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('order_position', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_position'),
        sa.UniqueConstraint('text'),
    )
    op.create_table(
        'style_prompts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=20), nullable=False),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('text'),
        sa.UniqueConstraint('title'),
    )
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=20), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('email_verified', sa.Boolean(), nullable=False),
        sa.Column('password_hash', sa.String(length=60), nullable=False),
        sa.Column(
            'role',
            sa.Enum('user', 'moderator', 'admin', name='user_role'),
            nullable=False,
        ),
        sa.Column(
            'logged_with_provider',
            sa.String(),
            nullable=True,
            comment='External OAuth provider name user has registered with',
        ),
        sa.Column(
            'provider_id',
            sa.String(),
            nullable=True,
            comment="User's ID from OAuth provider user has registered with",
        ),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_table(
        'articles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=50), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('language_id', sa.Integer(), nullable=True),
        sa.Column('original_article_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ['language_id'], ['languages.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['original_article_id'],
            ['articles.id'],
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('prompt_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=20), nullable=False),
        sa.Column(
            'language_ids', postgresql.ARRAY(sa.Integer()), nullable=False
        ),
        sa.Column('model_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ['model_id'], ['ai_models.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['prompt_id'], ['style_prompts.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'confirmation_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column(
            'code',
            sa.String(),
            nullable=False,
            comment='The value of the code',
        ),
        sa.Column(
            'reason',
            sa.Enum('registration', 'password_reset', name='confirmationtype'),
            nullable=False,
        ),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('expired_at', sa.DateTime(), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )
    op.create_table(
        'notifications',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column(
            'type',
            sa.Enum(
                'info', 'success', 'warning', 'error', name='notificationtype'
            ),
            nullable=False,
        ),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('ip', sa.String(length=15), nullable=False),
        sa.Column('user_agent', sa.String(length=100), nullable=False),
        sa.Column('is_closed', sa.Boolean(), nullable=False),
        sa.Column('refresh_token_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'reports',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('text', sa.String(length=1024), nullable=False),
        sa.Column('article_id', sa.UUID(), nullable=False),
        sa.Column(
            'status',
            sa.Enum(
                'open', 'closed', 'rejected', 'satisfied', name='reportstatus'
            ),
            nullable=False,
        ),
        sa.Column('closed_by_user_id', sa.UUID(), nullable=True),
        sa.Column('reason_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ['article_id'], ['articles.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['closed_by_user_id'], ['users.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['reason_id'],
            ['report_reasons.id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'translation_tasks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('article_id', sa.UUID(), nullable=False),
        sa.Column('target_language_id', sa.Integer(), nullable=False),
        sa.Column('prompt_id', sa.Integer(), nullable=False),
        sa.Column('model_id', sa.Integer(), nullable=False),
        sa.Column(
            'status',
            sa.Enum(
                'created',
                'started',
                'failed',
                'completed',
                name='translationtaskstatus',
            ),
            nullable=False,
        ),
        sa.Column(
            'data',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='Additional data related to the translation task (e.g., errors or metadata)',
        ),
        sa.Column('translated_article_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ['article_id'], ['articles.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['model_id'], ['ai_models.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['prompt_id'], ['style_prompts.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['target_language_id'],
            ['languages.id'],
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['translated_article_id'],
            ['articles.id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'report_comments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('text', sa.String(length=100), nullable=False),
        sa.Column('sender_id', sa.UUID(), nullable=False),
        sa.Column('report_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['report_id'], ['reports.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['sender_id'], ['users.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('report_comments')
    op.drop_table('translation_tasks')
    op.drop_table('reports')
    op.drop_table('sessions')
    op.drop_table('notifications')
    op.drop_table('confirmation_codes')
    op.drop_table('configs')
    op.drop_table('articles')
    op.drop_table('users')
    op.drop_table('style_prompts')
    op.drop_table('report_reasons')
    op.drop_table('languages')
    op.drop_table('ai_models')

    for enum_type in [
        'user_role',
        'confirmationtype',
        'notificationtype',
        'reportstatus',
        'translationtaskstatus',
    ]:
        op.execute(f'DROP TYPE IF EXISTS {enum_type}')
    # ### end Alembic commands ###
