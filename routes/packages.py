from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, exists
from sqlalchemy.orm import selectinload

from database import get_db
from models.package import Package, PackageCourse
from models.course import Course, UserCourse
from models.user import User
from models.module import Module
from models.lesson import Lesson
from utils.auth import get_current_user_id
from routes.activities import log_activity
from models.activity import ActivityType
from models.rating import CourseRating

router = APIRouter()


@router.get("/", response_model=list[dict])
async def list_packages(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Package).options(
            selectinload(Package.course_links).selectinload(PackageCourse.course)
        ).order_by(Package.level)
    )
    packages = result.scalars().all()

    package_ids = [pkg.id for pkg in packages]

    duration_result = await db.execute(
        select(
            PackageCourse.package_id,
            func.coalesce(func.sum(Lesson.duration_seconds), 0).label("total_duration_seconds"),
        )
        .join(Course, Course.id == PackageCourse.course_id)
        .join(Module, Module.course_id == Course.id)
        .join(Lesson, Lesson.module_id == Module.id)
        .where(PackageCourse.package_id.in_(package_ids))
        .group_by(PackageCourse.package_id)
    )
    durations = {row.package_id: row.total_duration_seconds for row in duration_result}

    rating_result = await db.execute(
        select(
            PackageCourse.package_id,
            func.avg(CourseRating.score).label("avg_rating"),
            func.count(CourseRating.id).label("review_count"),
        )
        .join(CourseRating, CourseRating.course_id == PackageCourse.course_id)
        .where(PackageCourse.package_id.in_(package_ids))
        .group_by(PackageCourse.package_id)
    )
    ratings = {row.package_id: row for row in rating_result}

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
        r = ratings.get(pkg.id)
        output.append({
            "id": pkg.slug,
            "title": pkg.title,
            "short_description": pkg.short_description,
            "level": pkg.level,
            "total_duration_seconds": durations.get(pkg.id, 0),
            "avg_rating": round(float(r.avg_rating), 1) if r and r.avg_rating else None,
            "review_count": r.review_count if r else 0,
            "courses": courses,
        })

    return output

@router.get("/enrolled", response_model=list[dict])
async def get_enrolled_packages(
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    enrolled_course_ids_sq = select(UserCourse.course_id).where(UserCourse.user_id == user.id)

    # Count how many courses in the package the user is enrolled in
    enrolled_count_sq = (
        select(func.count(PackageCourse.id))
        .where(
            PackageCourse.package_id == Package.id,
            PackageCourse.course_id.in_(enrolled_course_ids_sq),
        )
        .correlate(Package)
        .scalar_subquery()
    )

    # Count total courses in the package
    total_count_sq = (
        select(func.count(PackageCourse.id))
        .where(PackageCourse.package_id == Package.id)
        .correlate(Package)
        .scalar_subquery()
    )

    result = await db.execute(
        select(Package).options(
            selectinload(Package.course_links).selectinload(PackageCourse.course)
        )
        .where(enrolled_count_sq == total_count_sq, total_count_sq > 0)
        .order_by(Package.level)
    )
    packages = result.scalars().all()

    package_ids = [pkg.id for pkg in packages]

    duration_result = await db.execute(
        select(
            PackageCourse.package_id,
            func.coalesce(func.sum(Lesson.duration_seconds), 0).label("total_duration_seconds"),
        )
        .join(Course, Course.id == PackageCourse.course_id)
        .join(Module, Module.course_id == Course.id)
        .join(Lesson, Lesson.module_id == Module.id)
        .where(PackageCourse.package_id.in_(package_ids))
        .group_by(PackageCourse.package_id)
    )
    durations = {row.package_id: row.total_duration_seconds for row in duration_result}

    rating_result = await db.execute(
        select(
            PackageCourse.package_id,
            func.avg(CourseRating.score).label("avg_rating"),
            func.count(CourseRating.id).label("review_count"),
        )
        .join(CourseRating, CourseRating.course_id == PackageCourse.course_id)
        .where(PackageCourse.package_id.in_(package_ids))
        .group_by(PackageCourse.package_id)
    )
    ratings = {row.package_id: row for row in rating_result}

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
        r = ratings.get(pkg.id)
        output.append({
            "id": pkg.slug,
            "title": pkg.title,
            "short_description": pkg.short_description,
            "level": pkg.level,
            "total_duration_seconds": durations.get(pkg.id, 0),
            "avg_rating": round(float(r.avg_rating), 1) if r and r.avg_rating else None,
            "review_count": r.review_count if r else 0,
            "courses": courses,
        })

    return output


@router.post("/{slug}/enroll", status_code=200)
async def enroll_package(
    slug: str,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user_result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    pkg_result = await db.execute(
        select(Package)
        .options(selectinload(Package.course_links))
        .where(Package.slug == slug)
    )
    pkg = pkg_result.scalar_one_or_none()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")

    existing_result = await db.execute(
        select(UserCourse.course_id).where(
            UserCourse.user_id == user.id,
            UserCourse.course_id.in_([link.course_id for link in pkg.course_links]),
        )
    )
    already_enrolled = {row.course_id for row in existing_result}

    new_enrollments = [
        UserCourse(user_id=user.id, course_id=link.course_id)
        for link in pkg.course_links
        if link.course_id not in already_enrolled
    ]
    db.add_all(new_enrollments)
    await db.flush()

    if new_enrollments:
        await log_activity(
            db, user.id,
            type=ActivityType.package_enrolled,
            title=f'Enrolled in package "{pkg.title}"',
            metadata={"package_slug": slug},
        )

    return {"enrolled": len(new_enrollments), "already_enrolled": len(already_enrolled)}


@router.get("/{slug}")
async def get_package(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Package)
        .options(
            selectinload(Package.course_links).selectinload(PackageCourse.course)
        )
        .where(Package.slug == slug)
    )
    pkg = result.scalar_one_or_none()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")

    course_ids = [link.course_id for link in pkg.course_links]
    lesson_stats_result = await db.execute(
        select(
            Module.course_id,
            func.count(Lesson.id).label("total_lessons"),
            func.coalesce(func.sum(Lesson.duration_seconds), 0).label("total_duration_seconds"),
        )
        .join(Lesson, Lesson.module_id == Module.id)
        .where(Module.course_id.in_(course_ids))
        .group_by(Module.course_id)
    )
    lesson_stats = {row.course_id: row for row in lesson_stats_result}

    courses = [
        {
            "id": link.course.slug,
            "title": link.course.title,
            "image": link.course.thumbnail_url,
            "level": link.course.level,
            "total_lessons": lesson_stats[link.course_id].total_lessons if link.course_id in lesson_stats else 0,
            "total_duration_seconds": lesson_stats[link.course_id].total_duration_seconds if link.course_id in lesson_stats else 0,
            "courseNumber": f"Course {link.position} of {len(pkg.course_links)}",
        }
        for link in pkg.course_links
    ]

    return {
        "id": pkg.slug,
        "title": pkg.title,
        "short_description": pkg.short_description,
        "level": pkg.level,
        "courses": courses,
    }