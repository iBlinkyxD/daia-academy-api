"""seed badges

Revision ID: f1a2b3c4d5e6
Revises: e9c2d3a4b561
Create Date: 2026-03-24

"""
from alembic import op
import sqlalchemy as sa
import uuid

revision = 'f1a2b3c4d5e6'
down_revision = 'e9c2d3a4b561'
branch_labels = None
depends_on = None

BADGES = [
    {
        "id": str(uuid.uuid4()),
        "name": "AI 101",
        "description": "Completed the Artificial Intelligence fundamentals course.",
        "icon_url": "ai101",
        "criteria": "Complete the AI 101 course",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Communications 101",
        "description": "Completed the Communications fundamentals course.",
        "icon_url": "com101",
        "criteria": "Complete the Communications 101 course",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Databases 101",
        "description": "Completed the Databases fundamentals course.",
        "icon_url": "dbs101",
        "criteria": "Complete the Databases 101 course",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Dominican Republic 101",
        "description": "Completed the Dominican Republic culture and history course.",
        "icon_url": "dr101",
        "criteria": "Complete the DR 101 course",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "English 101",
        "description": "Completed the English language fundamentals course.",
        "icon_url": "eng101",
        "criteria": "Complete the English 101 course",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Spanish 101",
        "description": "Completed the Spanish language fundamentals course.",
        "icon_url": "esp101",
        "criteria": "Complete the Spanish 101 course",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Science 101",
        "description": "Completed the Science fundamentals course.",
        "icon_url": "sci101",
        "criteria": "Complete the Science 101 course",
    },
]


def upgrade() -> None:
    for b in BADGES:
        op.execute(
            sa.text(
                "INSERT INTO badges (id, name, description, icon_url, criteria) "
                "VALUES (CAST(:badge_id AS uuid), :name, :description, :icon_url, :criteria) "
                "ON CONFLICT (name) DO NOTHING"
            ).bindparams(
                badge_id=b["id"],
                name=b["name"],
                description=b["description"],
                icon_url=b["icon_url"],
                criteria=b["criteria"],
            )
        )


def downgrade() -> None:
    for b in BADGES:
        op.execute(
            sa.text("DELETE FROM badges WHERE name = :name").bindparams(name=b["name"])
        )
