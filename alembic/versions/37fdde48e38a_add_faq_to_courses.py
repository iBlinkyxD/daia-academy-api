"""add faq to courses

Revision ID: 37fdde48e38a
Revises: f322fd9eb8cb
Create Date: 2026-03-31 01:35:26.334793

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '37fdde48e38a'
down_revision: Union[str, None] = 'f322fd9eb8cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('courses', sa.Column('faq', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('courses', 'faq')
