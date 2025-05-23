"""empty message

Revision ID: 7c5052cccfa5
Revises: d140ada0b1dd
Create Date: 2025-03-11 11:04:48.827639

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c5052cccfa5'
down_revision: Union[str, None] = 'd140ada0b1dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('translation_tasks', sa.Column('cost', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('translation_tasks', 'cost')
    # ### end Alembic commands ###
