"""add badge_url to courses

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-03-24

"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None

BADGES = ['ai101', 'com101', 'dbs101', 'dr101', 'eng101', 'esp101', 'sci101']


def upgrade() -> None:
    op.add_column('courses', sa.Column('badge_url', sa.String(100), nullable=True))

    # Randomly assign one of the 7 badge keys to each existing course
    op.execute(
        sa.text("""
            UPDATE courses
            SET badge_url = (
                ARRAY['ai101','com101','dbs101','dr101','eng101','esp101','sci101']
            )[floor(random() * 7 + 1)::int]
        """)
    )


def downgrade() -> None:
    op.drop_column('courses', 'badge_url')
