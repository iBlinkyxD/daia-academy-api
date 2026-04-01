"""short_description to text

Revision ID: f322fd9eb8cb
Revises: b2c3d4e5f6a7
Create Date: 2026-03-31 01:20:05.536658

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'f322fd9eb8cb'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('courses', 'short_description',
               existing_type=sa.VARCHAR(length=500),
               type_=sa.Text(),
               existing_nullable=True)


def downgrade() -> None:
    op.alter_column('courses', 'short_description',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(length=500),
               existing_nullable=True)
