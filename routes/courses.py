import json
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from database import get_db
from models.user import User
from models.course import Course, UserCourse, CourseProgress
from models.module import Module
from models.lesson import Lesson
from models.rating import CourseRating
from schemas.course import CourseCreate, CourseRead, UserCourseRead, CourseProgressRead, LessonRead, ModuleRead, CourseDetailRead, AdminCourseRead, RatingSubmit
from utils.auth import get_current_user_id
from config import settings
from routes.activities import log_activity
from models.activity import ActivityType

router = APIRouter()


@router.get("/", response_model=list[CourseRead])
async def list_courses(db: AsyncSession = Depends(get_db)):
    lesson_count_sq = (
        select(func.count(Lesson.id))
        .join(Module, Module.id == Lesson.module_id)
        .where(Module.course_id == Course.id)
        .scalar_subquery()
    )

    duration_sq = (
        select(func.coalesce(func.sum(Lesson.duration_seconds), 0))
        .join(Module, Module.id == Lesson.module_id)
        .where(Module.course_id == Course.id)
        .scalar_subquery()
    )

    enrollment_count_sq = (
        select(func.count(UserCourse.id))
        .where(UserCourse.course_id == Course.id)
        .scalar_subquery()
    )

    avg_rating_sq = (
        select(func.avg(CourseRating.score))
        .where(CourseRating.course_id == Course.id)
        .scalar_subquery()
    )

    review_count_sq = (
        select(func.count(CourseRating.id))
        .where(CourseRating.course_id == Course.id)
        .scalar_subquery()
    )

    result = await db.execute(
        select(
            Course,
            lesson_count_sq.label("total_lessons"),
            duration_sq.label("total_duration_seconds"),
            enrollment_count_sq.label("enrollment_count"),
            avg_rating_sq.label("avg_rating"),
            review_count_sq.label("review_count"),
        )
        .where(Course.is_published == True)
        .order_by(Course.created_at.desc())
    )

    rows = result.all()

    courses = []
    for row in rows:
        course = row.Course
        course.total_lessons = row.total_lessons or 0
        course.total_duration_seconds = row.total_duration_seconds or 0
        course.enrollment_count = row.enrollment_count or 0
        course.avg_rating = round(float(row.avg_rating), 1) if row.avg_rating else None
        course.review_count = row.review_count or 0
        courses.append(course)

    return courses


@router.get("/admin/all", response_model=list[AdminCourseRead])
async def admin_list_courses(
    _: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    module_count_sq = (
        select(func.count(Module.id))
        .where(Module.course_id == Course.id)
        .scalar_subquery()
    )

    lesson_count_sq = (
        select(func.count(Lesson.id))
        .join(Module, Module.id == Lesson.module_id)
        .where(Module.course_id == Course.id)
        .scalar_subquery()
    )

    has_video_sq = (
        select(func.count(Lesson.id))
        .join(Module, Module.id == Lesson.module_id)
        .where(Module.course_id == Course.id, Lesson.video_url.isnot(None))
        .scalar_subquery()
    )

    enrollment_count_sq = (
        select(func.count(UserCourse.id))
        .where(UserCourse.course_id == Course.id)
        .scalar_subquery()
    )

    result = await db.execute(
        select(
            Course,
            module_count_sq.label("module_count"),
            lesson_count_sq.label("total_lessons"),
            has_video_sq.label("video_count"),
            enrollment_count_sq.label("enrollment_count"),
        )
        .order_by(Course.created_at.desc())
    )

    rows = result.all()
    courses = []
    for row in rows:
        course = row.Course
        course.module_count = row.module_count or 0
        course.total_lessons = row.total_lessons or 0
        course.has_video = (row.video_count or 0) > 0
        course.enrollment_count = row.enrollment_count or 0
        courses.append(course)

    return courses


@router.post("/", response_model=CourseRead, status_code=201)
async def create_course(
    payload: CourseCreate,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    course = Course(**payload.model_dump())
    db.add(course)
    await db.flush()
    await db.refresh(course)
    return course


@router.get("/enrolled", response_model=list[CourseRead])
async def get_enrolled_courses(
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    lesson_count_sq = (
        select(func.count(Lesson.id))
        .join(Module, Module.id == Lesson.module_id)
        .where(Module.course_id == Course.id)
        .correlate(Course)
        .scalar_subquery()
    )
    duration_sq = (
        select(func.coalesce(func.sum(Lesson.duration_seconds), 0))
        .join(Module, Module.id == Lesson.module_id)
        .where(Module.course_id == Course.id)
        .correlate(Course)
        .scalar_subquery()
    )
    enrollment_count_sq = (
        select(func.count(UserCourse.id))
        .where(UserCourse.course_id == Course.id)
        .correlate(Course)
        .scalar_subquery()
    )
    avg_rating_sq = (
        select(func.avg(CourseRating.score))
        .where(CourseRating.course_id == Course.id)
        .correlate(Course)
        .scalar_subquery()
    )
    review_count_sq = (
        select(func.count(CourseRating.id))
        .where(CourseRating.course_id == Course.id)
        .correlate(Course)
        .scalar_subquery()
    )

    rows_result = await db.execute(
        select(
            Course,
            lesson_count_sq.label("total_lessons"),
            duration_sq.label("total_duration_seconds"),
            enrollment_count_sq.label("enrollment_count"),
            avg_rating_sq.label("avg_rating"),
            review_count_sq.label("review_count"),
        )
        .join(UserCourse, UserCourse.course_id == Course.id)
        .where(UserCourse.user_id == user.id, Course.is_published == True)
        .order_by(Course.created_at.desc())
    )

    courses = []
    for row in rows_result.all():
        course = row.Course
        course.total_lessons = row.total_lessons or 0
        course.total_duration_seconds = row.total_duration_seconds or 0
        course.enrollment_count = row.enrollment_count or 0
        course.avg_rating = round(float(row.avg_rating), 1) if row.avg_rating else None
        course.review_count = row.review_count or 0
        courses.append(course)

    return courses


@router.post("/{course_id}/enroll", response_model=UserCourseRead, status_code=201)
async def enroll(
    course_id: UUID,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    enrollment = UserCourse(user_id=user.id, course_id=course_id)
    db.add(enrollment)
    await db.flush()
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalar_one_or_none()
    await log_activity(
        db, user.id,
        type=ActivityType.course_enrolled,
        title=f'Enrolled in "{course.title}"' if course else "Enrolled in a course",
        metadata={"course_id": str(course_id)},
    )
    await db.refresh(enrollment)
    return enrollment


@router.get("/{course_id}/progress", response_model=CourseProgressRead)
async def get_progress(
    course_id: UUID,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    res = await db.execute(
        select(CourseProgress).where(
            CourseProgress.user_id == user.id, CourseProgress.course_id == course_id
        )
    )
    progress = res.scalar_one_or_none()
    if not progress:
        raise HTTPException(status_code=404, detail="No progress yet")
    return progress

# ── AI Course Generation ───────────────────────────────────────────────────────

class CourseGenerateRequest(BaseModel):
    description: str
    level: str
    language: str
    duration: str
    module_count: int
    avg_lessons_per_module: int
    avg_lesson_length: int
    include_assessments: bool
    include_projects: bool
    course_code: str = ""
    badge_name: str = ""


class LessonOutline(BaseModel):
    name: str
    overview: str


class ModuleOutline(BaseModel):
    title: str
    lessons: list[LessonOutline]


class CourseGenerateResponse(BaseModel):
    title: str
    short_description: str
    modules: list[ModuleOutline]
    faq: str


_AI_SYSTEM_PROMPT = """You are a curriculum architect for DAIA Academy, an AI education platform in the Dominican Republic targeting students ages 14 and up.

Generate a structured course outline based on the provided description and configuration.

TONE: Conversational, clear, and energetic — like a knowledgeable teacher who respects the student's intelligence. Use real-world examples relevant to the Dominican Republic and Latin America where natural.

OUTPUT FORMAT:
Return a single valid JSON object only. No markdown fences, no extra text.

{
  "title": "clear and specific course title",
  "short_description": "2–3 sentence description of what students will learn and why it matters",
  "modules": [
    {
      "title": "module title — forms a logical step in the learning journey",
      "lessons": [
        {
          "name": "lesson name — specific and action-oriented",
          "overview": "2–3 paragraph lesson overview in plain prose (no markdown headers). First paragraph introduces the topic, second covers key concepts, third explains practical application or takeaway."
        }
      ]
    }
  ],
  "faq": "FAQ in markdown: start with ## Frequently Asked Questions, then 5–7 Q&A pairs using **Q:** and **A:** format separated by blank lines"
}

RULES:
- Generate EXACTLY the number of modules and lessons per module specified — no more, no less
- Module titles must form a clear logical progression from fundamentals to advanced topics
- Lesson names must be specific (avoid generic names like "Introduction" or "Overview")
- Each lesson overview must be 120–180 words
- If assessments are requested, make the last lesson of each module a quiz/review lesson
- If projects are requested, make the last lesson of the last module a capstone project
- Do NOT include any text outside the JSON object"""


@router.post("/ai-generate", response_model=CourseGenerateResponse)
async def ai_generate_course(
    payload: CourseGenerateRequest,
    _: UUID = Depends(get_current_user_id),
):
    api_key = settings.ANTHROPIC_API_KEY
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

    try:
        import anthropic
    except ImportError:
        raise HTTPException(status_code=500, detail="anthropic package not installed — run: pip install anthropic")

    lang_note = {
        "english": "Write all content in English.",
        "spanish": "Write all content in Spanish.",
        "bilingual": "Write content in English; include Spanish equivalents for key terms where helpful.",
    }.get(payload.language, "Write all content in English.")

    extras: list[str] = []
    if payload.include_assessments:
        extras.append("Make the last lesson of each module a quiz or knowledge-check review lesson.")
    if payload.include_projects:
        extras.append("Make the last lesson of the final module a hands-on capstone project lesson.")

    user_message = f"""Generate a course outline with these exact specifications:

Description: {payload.description}
Level: {payload.level}
Language: {payload.language} — {lang_note}
Duration: {payload.duration}
Number of modules: {payload.module_count} (generate EXACTLY this many)
Lessons per module: {payload.avg_lessons_per_module} (generate EXACTLY this many in each module)
Average lesson length: {payload.avg_lesson_length} minutes
{chr(10).join(extras)}

Return only the JSON object."""

    client = anthropic.AsyncAnthropic(api_key=api_key)
    message = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        system=_AI_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = message.content[0].text.strip()
    # Strip markdown fences if the model wraps its output anyway
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"AI returned invalid JSON: {exc}")

    return data


@router.get("/{slug}", response_model=CourseDetailRead)
async def get_course(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Course)
        .options(
            selectinload(Course.modules).selectinload(Module.lessons)
        )
        .where(Course.slug == slug, Course.is_published == True)
    )
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    count_result = await db.execute(
        select(func.count(UserCourse.id)).where(UserCourse.course_id == course.id)
    )
    course.enrollment_count = count_result.scalar() or 0

    rating_result = await db.execute(
        select(func.avg(CourseRating.score), func.count(CourseRating.id))
        .where(CourseRating.course_id == course.id)
    )
    avg, count = rating_result.one()
    course.avg_rating = round(float(avg), 1) if avg else None
    course.review_count = count or 0

    return course


@router.post("/{slug}/rate", status_code=204)
async def rate_course(
    slug: str,
    payload: RatingSubmit,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    if payload.score < 1 or payload.score > 5:
        raise HTTPException(status_code=422, detail="Score must be between 1 and 5")

    course_result = await db.execute(select(Course).where(Course.slug == slug))
    course = course_result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    user_result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = await db.execute(
        select(CourseRating).where(
            CourseRating.user_id == user.id, CourseRating.course_id == course.id
        )
    )
    rating = existing.scalar_one_or_none()
    if rating:
        rating.score = payload.score
    else:
        db.add(CourseRating(user_id=user.id, course_id=course.id, score=payload.score))