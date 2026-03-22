from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import get_db
from models.package import Package, PackageCourse
from models.course import Course

router = APIRouter()


@router.get("/", response_model=list[dict])
async def list_packages(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Package).options(
            selectinload(Package.course_links).selectinload(PackageCourse.course)
        ).order_by(Package.level)
    )
    packages = result.scalars().all()

    output = []
    for pkg in packages:
        courses = [
            {
                "id": link.course.slug,
                "title": link.course.title,
                "image": link.course.thumbnail_url,
                "courseNumber": f"Course {link.position} of {len(pkg.course_links)}",
            }
            for link in pkg.course_links
        ]
        output.append({
            "id": pkg.slug,
            "title": pkg.title,
            "short_description": pkg.short_description,
            "level": pkg.level,
            "courses": courses,
        })

    return output