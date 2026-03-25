"""add user_activities table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-25

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type only if it doesn't exist (create_all may have already created it)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE activitytype AS ENUM (
                'lesson_completed', 'badge_earned', 'course_enrolled', 'package_enrolled',
                'post_created', 'post_liked', 'post_commented', 'user_followed'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.create_table(
        "user_activities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("type", sa.Enum(
            "lesson_completed", "badge_earned", "course_enrolled", "package_enrolled",
            "post_created", "post_liked", "post_commented", "user_followed",
            name="activitytype",
            create_type=False,
        ), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("xp_earned", sa.Integer, nullable=False, server_default="0"),
        sa.Column("extra", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_user_activities_user_id", "user_activities", ["user_id"])
    op.create_index("ix_user_activities_created_at", "user_activities", ["created_at"])


def downgrade() -> None:
    op.drop_table("user_activities")
    op.execute("DROP TYPE IF EXISTS activitytype")