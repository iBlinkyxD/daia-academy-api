"""add instructor_name to courses

Revision ID: e9c2d3a4b561
Revises: d7b4e1f2a983
Create Date: 2026-03-24 00:02:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e9c2d3a4b561'
down_revision: Union[str, None] = 'd7b4e1f2a983'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('courses', sa.Column('instructor_name', sa.String(length=200), nullable=True))


def downgrade() -> None:
    op.drop_column('courses', 'instructor_name')
