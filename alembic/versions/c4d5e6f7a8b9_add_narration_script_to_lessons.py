"""add narration_script to lessons

Revision ID: c4d5e6f7a8b9
Revises: 37fdde48e38a
Create Date: 2026-03-31 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, None] = '37fdde48e38a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('lessons', sa.Column('narration_script', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('lessons', 'narration_script')
