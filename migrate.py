"""
Startup migration script.

- If no alembic_version row exists, the DB was bootstrapped by create_all
  (all tables already exist at current schema). Stamp to head so alembic
  knows where we are, then upgrade is a no-op.
- If a version row exists, run upgrade head normally to apply any new migrations.
"""
import asyncio
import subprocess
import sys
from sqlalchemy import text
from database import engine


async def _has_alembic_version() -> bool:
    async with engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT EXISTS ("
                "  SELECT 1 FROM information_schema.tables"
                "  WHERE table_name = 'alembic_version'"
                ")"
            )
        )
        table_exists = result.scalar()
        if not table_exists:
            return False
        result = await conn.execute(text("SELECT COUNT(*) FROM alembic_version"))
        return (result.scalar() or 0) > 0


def run(cmd: list[str]) -> None:
    print(f">> {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(result.returncode)


if __name__ == "__main__":
    has_version = asyncio.run(_has_alembic_version())

    if has_version:
        print("Alembic version found — running upgrade head", flush=True)
        run(["alembic", "upgrade", "head"])
    else:
        print("No alembic version — stamping DB to head (tables exist from create_all)", flush=True)
        run(["alembic", "stamp", "head"])
        print("Stamp complete — future deploys will use upgrade head", flush=True)