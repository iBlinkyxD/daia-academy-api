"""add course_ratings table

Revision ID: d7b4e1f2a983
Revises: c3f1a2b9d4e7
Create Date: 2026-03-24 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd7b4e1f2a983'
down_revision: Union[str, None] = 'c3f1a2b9d4e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'course_ratings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('course_id', sa.UUID(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'course_id', name='uq_course_rating'),
    )
    op.create_index(op.f('ix_course_ratings_course_id'), 'course_ratings', ['course_id'])
    op.create_index(op.f('ix_course_ratings_user_id'), 'course_ratings', ['user_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_course_ratings_user_id'), table_name='course_ratings')
    op.drop_index(op.f('ix_course_ratings_course_id'), table_name='course_ratings')
    op.drop_table('course_ratings')
