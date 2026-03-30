#!/usr/bin/env python3
"""
DAIA Academy — AI-powered course/module/lesson generator.

Creates a full course → module → lesson chain, generating lesson content
via Claude, then POSTing everything to the academy API.

Usage (full creation):
    python scripts/seed_lesson.py \\
        --course_title "AI Foundations" \\
        --course_slug "ai-foundations" \\
        --course_level beginner \\
        --module_title "Introduction to AI" \\
        --topic "What Is AI, Really?" \\
        --position 1 \\
        --publish

Usage (existing course + module, just generate lesson):
    python scripts/seed_lesson.py \\
        --course_id <uuid> \\
        --module_id <uuid> \\
        --topic "What Is AI, Really?" \\
        --position 1

Env vars (loaded from .env automatically):
    ANTHROPIC_API_KEY
    API_TOKEN           — access_token cookie from the academy app
    API_URL             — default: http://localhost:8001
"""

import argparse
import json
import os
import re
import sys

import httpx

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv optional; env vars can be set manually

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic package not installed. Run: pip install anthropic")
    sys.exit(1)


# ── Helpers ────────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text


def api_headers_and_cookies() -> tuple[dict, dict]:
    token = os.environ.get("API_TOKEN")
    if not token:
        print("ERROR: API_TOKEN environment variable not set.")
        sys.exit(1)
    return {}, {"access_token": token}


def base_url() -> str:
    return os.environ.get("API_URL", "http://localhost:8001").rstrip("/")


def post(path: str, payload: dict) -> dict:
    headers, cookies = api_headers_and_cookies()
    url = f"{base_url()}{path}"
    with httpx.Client() as client:
        response = client.post(url, json=payload, headers=headers, cookies=cookies, timeout=30.0)
    if response.status_code not in (200, 201):
        print(f"ERROR: POST {path} returned {response.status_code}\n{response.text}")
        sys.exit(1)
    return response.json()


# ── Step 1: Create course ──────────────────────────────────────────────────────

def create_course(args) -> str:
    if args.course_id:
        print(f"Using existing course: {args.course_id}")
        return args.course_id

    slug = args.course_slug or slugify(args.course_title)
    payload = {
        "title": args.course_title,
        "slug": slug,
        "level": args.course_level,
        "description": args.course_description,
        "short_description": args.course_short_description,
        "instructor_name": args.instructor_name,
        "thumbnail_url": args.thumbnail_url,
        "is_published": args.publish,
    }
    print(f"Creating course: '{args.course_title}' (slug: {slug}) ...")
    result = post("/courses/", payload)
    course_id = result["id"]
    print(f"  ✓ Course created — ID: {course_id}")
    return course_id


# ── Step 2: Create module ──────────────────────────────────────────────────────

def create_module(course_id: str, args) -> str:
    if args.module_id:
        print(f"Using existing module: {args.module_id}")
        return args.module_id

    payload = {
        "course_id": course_id,
        "title": args.module_title,
        "description": args.module_description,
        "position": args.module_position,
    }
    print(f"Creating module: '{args.module_title}' ...")
    result = post("/modules/", payload)
    module_id = result["id"]
    print(f"  ✓ Module created — ID: {module_id}")
    return module_id


# ── Step 3: Generate lesson content via Claude ─────────────────────────────────

SYSTEM_PROMPT = """You are a curriculum writer for DAIA (Dominican Artificial Intelligence Association).
You write lessons for Course 1: AI Foundations — Standard Track, aimed at ages 14 and up in the Dominican Republic.

TONE & STYLE:
- Conversational and energetic, like a knowledgeable teacher who respects the student's intelligence
- Direct and clear — no filler, no fluff
- Confident but never condescending
- Acknowledge the bilingual (EN/ES) context of your students where natural

CONTENT STANDARDS:
- Every concept must be grounded in real, accurate information
- Use concrete, everyday examples relevant to students in the Dominican Republic and Latin America
- Avoid US-centric cultural references where possible; prefer universal or regional ones
- Where AI hype exists, address it honestly

OUTPUT FORMAT:
Respond with a single valid JSON object only. No markdown fences, no extra text.

{
  "title": "string — lesson title, clear and specific",
  "duration_seconds": integer — estimated reading/viewing time in seconds (300–600 typical),
  "lesson_type": "video",
  "objectives": [
    "string — starts with an action verb (Define, Identify, Explain, Compare...)",
    "3 to 5 objectives total"
  ],
  "content": "string — full written lesson body in Markdown. Must include:\\n- Opening hook paragraph\\n- 2–4 sections with ## headings\\n- Concrete examples in each section\\n- Summary paragraph at the end\\n- Minimum 400 words, target 600–800 words",
  "vocabulary": [
    {
      "term": "English term",
      "term_es": "Spanish equivalent",
      "definition": "Plain-language definition. 1–2 sentences max."
    }
  ]
}

RULES:
- 3–5 vocabulary entries, only terms that appear in the content
- 3–5 objectives, each measurable
- Do not include any text outside the JSON object"""


def generate_lesson(topic: str, position: int) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    user_message = (
        f"Write a complete DAIA Course 1 Standard Track lesson on:\n\n"
        f"Topic: {topic}\n"
        f"Lesson position: {position}\n\n"
        f"Return only the JSON object."
    )

    print(f"Calling Claude (claude-sonnet-4-6) for topic: '{topic}' ...")
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = message.content[0].text.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: Claude returned invalid JSON.\n{e}\n\nRaw:\n{raw}")
        sys.exit(1)

    required = {"title", "duration_seconds", "lesson_type", "objectives", "content", "vocabulary"}
    missing = required - data.keys()
    if missing:
        print(f"ERROR: Claude response missing fields: {missing}")
        sys.exit(1)

    return data


# ── Step 4: Create lesson ──────────────────────────────────────────────────────

def create_lesson(module_id: str, position: int, lesson_data: dict) -> str:
    payload = {
        "module_id": module_id,
        "title": lesson_data["title"],
        "content": lesson_data["content"],
        "video_url": None,
        "duration_seconds": lesson_data["duration_seconds"],
        "lesson_type": lesson_data["lesson_type"],
        "position": position,
        "objectives": lesson_data["objectives"],
        "vocabulary": lesson_data["vocabulary"],
    }
    print(f"Creating lesson: '{lesson_data['title']}' ...")
    result = post("/lessons/", payload)
    lesson_id = result["id"]
    print(f"  ✓ Lesson created — ID: {lesson_id}")
    return lesson_id


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate and seed a DAIA Academy course, module, and lesson."
    )

    # Course args
    course = parser.add_argument_group("Course (skip with --course_id)")
    course.add_argument("--course_id", help="Use an existing course UUID instead of creating one.")
    course.add_argument("--course_title", help="Course title.")
    course.add_argument("--course_slug", help="Course slug (auto-generated from title if omitted).")
    course.add_argument("--course_level", default="beginner", choices=["beginner", "intermediate", "advanced"])
    course.add_argument("--course_description", default=None)
    course.add_argument("--course_short_description", default=None)
    course.add_argument("--instructor_name", default="DAIA Academy")
    course.add_argument("--thumbnail_url", default=None)
    course.add_argument("--publish", action="store_true", help="Publish the course immediately.")

    # Module args
    module = parser.add_argument_group("Module (skip with --module_id)")
    module.add_argument("--module_id", help="Use an existing module UUID instead of creating one.")
    module.add_argument("--module_title", help="Module title.")
    module.add_argument("--module_description", default=None)
    module.add_argument("--module_position", type=int, default=1)

    # Lesson args
    lesson = parser.add_argument_group("Lesson")
    lesson.add_argument("--topic", required=True, help='Lesson topic, e.g. "What Is AI, Really?"')
    lesson.add_argument("--position", type=int, default=1, help="Lesson position within the module.")

    args = parser.parse_args()

    # Validate
    if not args.course_id and not args.course_title:
        parser.error("Either --course_id or --course_title is required.")
    if not args.module_id and not args.module_title:
        parser.error("Either --module_id or --module_title is required.")

    print("\n── DAIA Lesson Seeder ──────────────────────────────")

    course_id = create_course(args)
    module_id = create_module(course_id, args)
    lesson_data = generate_lesson(args.topic, args.position)

    print(f"\n  Generated: '{lesson_data['title']}'")
    print(f"  Objectives : {len(lesson_data['objectives'])}")
    print(f"  Vocabulary : {len(lesson_data['vocabulary'])} terms")
    print(f"  Duration   : {lesson_data['duration_seconds']}s")
    print(f"  Content    : {len(lesson_data['content'])} chars\n")

    lesson_id = create_lesson(module_id, args.position, lesson_data)

    print("\n────────────────────────────────────────────────────")
    print(f"  Course ID : {course_id}")
    print(f"  Module ID : {module_id}")
    print(f"  Lesson ID : {lesson_id}")
    print("────────────────────────────────────────────────────\n")


if __name__ == "__main__":
    main()
