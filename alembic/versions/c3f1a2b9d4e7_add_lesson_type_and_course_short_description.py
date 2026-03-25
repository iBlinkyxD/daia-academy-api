"""add lesson_type and course short_description

Revision ID: c3f1a2b9d4e7
Revises: 7e20dba6c806
Create Date: 2026-03-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3f1a2b9d4e7'
down_revision: Union[str, None] = '7e20dba6c806'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

lessontype_enum = sa.Enum('video', 'article', 'quiz', 'assignment', name='lessontype')


def upgrade() -> None:
    # Create the enum type if it doesn't already exist
    lessontype_enum.create(op.get_bind(), checkfirst=True)

    # Add lesson_type to lessons (default to 'article' for existing rows)
    op.add_column(
        'lessons',
        sa.Column(
            'lesson_type',
            lessontype_enum,
            nullable=False,
            server_default='article',
        ),
    )

    # Add short_description to courses
    op.add_column(
        'courses',
        sa.Column('short_description', sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('courses', 'short_description')
    op.drop_column('lessons', 'lesson_type')
