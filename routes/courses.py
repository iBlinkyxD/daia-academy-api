import asyncio
import json
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from services.storage import upload_thumbnail
from fastapi.responses import StreamingResponse
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


@router.patch("/{slug}/publish", status_code=204)
async def publish_course(
    slug: str,
    _: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Course).where(Course.slug == slug))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    course.is_published = True
    await db.commit()


@router.post("/{slug}/thumbnail", status_code=200)
async def upload_course_thumbnail(
    slug: str,
    file: UploadFile = File(...),
    _: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Course).where(Course.slug == slug))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    file_bytes = await file.read()
    public_url = await upload_thumbnail(
        file_bytes=file_bytes,
        filename=file.filename or "thumbnail.jpg",
        content_type=file.content_type or "image/jpeg",
        course_slug=slug,
    )
    course.thumbnail_url = public_url
    await db.commit()
    return {"thumbnail_url": public_url}


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
    estimated_output_tokens: int = 8000


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
          "overview": "Lesson content in markdown. Use ## for section headers, bullet lists for key points or steps, **bold** for important terms, and short paragraphs. Structure: an intro section, a key concepts section with bullets or sub-headers, and a practical application or takeaway section.",
          "objectives": ["learning objective 1", "learning objective 2"],
          "vocabulary": [{"term": "Term", "definition": "What it means"}]
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
- Each lesson overview length is specified in the user message — follow it precisely
- "objectives": 3–5 strings describing what the student will be able to do after this lesson. Include when the lesson teaches a skill, process, or concept students need to apply. OMIT for review, quiz, or project lessons.
- "vocabulary": array of {term, definition} objects. Include only for lessons that introduce domain-specific terminology students haven't seen yet. OMIT if the lesson has no new technical terms.
- Both objectives and vocabulary are optional — only include them when they genuinely add value for that specific lesson
- If assessments are requested, make the last lesson of each module a quiz/review lesson
- If projects are requested, make the last lesson of the last module a capstone project
- Do NOT include any text outside the JSON object"""


@router.post("/ai-generate")
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

    words_per_lesson = payload.avg_lesson_length * 150

    user_message = f"""Generate a course outline with these exact specifications:

Description: {payload.description}
Level: {payload.level}
Language: {payload.language} — {lang_note}
Duration: {payload.duration}
Number of modules: {payload.module_count} (generate EXACTLY this many)
Lessons per module: {payload.avg_lessons_per_module} (generate EXACTLY this many in each module)
Average lesson length: {payload.avg_lesson_length} minutes
{chr(10).join(extras)}

Content calibration:
Each lesson's overview should be calibrated to {payload.avg_lesson_length} minutes of reading time.
At 150 words per minute average reading speed, each lesson overview body should be approximately {words_per_lesson} words.

Return only the JSON object."""

    dynamic_max_tokens = min(64_000, max(8_000, int(payload.estimated_output_tokens * 1.6)))
    client = anthropic.AsyncAnthropic(api_key=api_key, timeout=None)

    async def generate():
        for attempt in range(3):
            try:
                async with client.messages.stream(
                    model="claude-sonnet-4-6",
                    max_tokens=dynamic_max_tokens,
                    system=_AI_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_message}],
                ) as stream:
                    async for text in stream.text_stream:
                        yield f"data: {json.dumps(text)}\n\n"
                yield "data: [DONE]\n\n"
                return
            except anthropic.APIStatusError as exc:
                if exc.status_code == 529 and attempt < 2:
                    await asyncio.sleep(5 * (2 ** attempt))
                    continue
                yield f"data: [ERROR] {exc.message}\n\n"
                return
            except Exception as exc:
                yield f"data: [ERROR] {str(exc)}\n\n"
                return

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


_AI_NARRATION_SYSTEM_PROMPT = """You are a narration script writer for DAIA Academy, an AI education platform in the Dominican Republic targeting students ages 14 and up.

You will receive a structured course outline (title, modules, and per-lesson written overviews) and must produce a spoken narration script for each lesson that is consistent with and expands naturally on the written overview.

TONE: Warm, direct, and conversational — as if a knowledgeable teacher is speaking aloud to a student. Contractions are fine. Avoid bullet points and headers in narration.

OUTPUT FORMAT:
Return a single valid JSON object only. No markdown fences, no extra text.

{
  "modules": [
    {
      "title": "exact module title from input",
      "lessons": [
        {
          "name": "exact lesson name from input",
          "narration": "full narration script as flowing prose, no markdown"
        }
      ]
    }
  ]
}

RULES:
- Generate narration for EVERY lesson in every module — same count as input
- Each narration must be calibrated to the target reading time (specified in user message)
- Narration must feel coherent with the lesson's written overview — same key points, different voice
- Do NOT copy the written overview verbatim — rephrase for spoken delivery
- Do NOT include any text outside the JSON object"""


class NarrationLessonInput(BaseModel):
    name: str
    overview: str


class NarrationModuleInput(BaseModel):
    title: str
    lessons: list[NarrationLessonInput]


class NarrationGenerateRequest(BaseModel):
    course_title: str
    short_description: str
    avg_lesson_length: int
    language: str
    modules: list[NarrationModuleInput]
    estimated_output_tokens: int = 8000


class NarrationLessonOutput(BaseModel):
    name: str
    narration: str


class NarrationModuleOutput(BaseModel):
    title: str
    lessons: list[NarrationLessonOutput]


class NarrationGenerateResponse(BaseModel):
    modules: list[NarrationModuleOutput]


@router.post("/ai-narrate")
async def ai_narrate_course(
    payload: NarrationGenerateRequest,
    _: UUID = Depends(get_current_user_id),
):
    api_key = settings.ANTHROPIC_API_KEY
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

    try:
        import anthropic
    except ImportError:
        raise HTTPException(status_code=500, detail="anthropic package not installed")

    lang_note = {
        "english": "Write all narration in English.",
        "spanish": "Write all narration in Spanish.",
        "bilingual": "Write narration in English; include Spanish equivalents for key terms where natural.",
    }.get(payload.language, "Write all narration in English.")

    words_per_narration = payload.avg_lesson_length * 130

    context_lines = [
        f"Course: {payload.course_title}",
        f"Description: {payload.short_description}",
        "",
        "Written lesson overviews (use as reference — do NOT copy verbatim):",
    ]
    for mi, mod in enumerate(payload.modules):
        context_lines.append(f"\nModule {mi + 1}: {mod.title}")
        for li, lesson in enumerate(mod.lessons):
            context_lines.append(f"  Lesson {li + 1}: {lesson.name}")
            context_lines.append(f"  Overview: {lesson.overview}")

    user_message = f"""{chr(10).join(context_lines)}

---

Now write narration scripts for every lesson above.

Language: {payload.language} — {lang_note}
Target narration length per lesson: {payload.avg_lesson_length} minutes spoken
At 130 words per minute speaking pace, each narration should be approximately {words_per_narration} words.

Return only the JSON object."""

    dynamic_max_tokens = min(64_000, max(8_000, int(payload.estimated_output_tokens * 1.6)))
    client = anthropic.AsyncAnthropic(api_key=api_key, timeout=None)

    async def generate():
        for attempt in range(3):
            try:
                async with client.messages.stream(
                    model="claude-sonnet-4-6",
                    max_tokens=dynamic_max_tokens,
                    system=_AI_NARRATION_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_message}],
                ) as stream:
                    async for text in stream.text_stream:
                        yield f"data: {json.dumps(text)}\n\n"
                yield "data: [DONE]\n\n"
                return
            except anthropic.APIStatusError as exc:
                if exc.status_code == 529 and attempt < 2:
                    await asyncio.sleep(5 * (2 ** attempt))
                    continue
                yield f"data: [ERROR] {exc.message}\n\n"
                return
            except Exception as exc:
                yield f"data: [ERROR] {str(exc)}\n\n"
                return

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/admin/{slug}", response_model=CourseDetailRead)
async def admin_get_course(
    slug: str,
    _: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Course)
        .options(selectinload(Course.modules).selectinload(Module.lessons))
        .where(Course.slug == slug)
    )
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    count_result = await db.execute(
        select(func.count(UserCourse.id)).where(UserCourse.course_id == course.id)
    )
    course.enrollment_count = count_result.scalar() or 0
    course.avg_rating = None
    course.review_count = 0
    return course


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