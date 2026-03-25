import os
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database import engine, Base
from routes import (
    users, spaces, posts, comments, courses,
    modules, lessons, events, chats, notifications, badges, packages, activities
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="DAIA Academy API",
    description="API for DAIA Academy — courses, spaces, events, and community features.",
    version="1.0.0",
    lifespan=lifespan,
)

_default_origins = ["http://localhost:8082"]
_cors_env = os.getenv("CORS_ORIGINS", "").strip()
_cors = (
    [o.strip() for o in _cors_env.split(",") if o.strip()]
    if _cors_env
    else _default_origins
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8082","https://daia-academy-app.netlify.app"],  # your frontend URL, not wildcard "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(users.router,        prefix="/users",         tags=["Users"])
app.include_router(spaces.router,       prefix="/spaces",        tags=["Spaces"])
app.include_router(posts.router,        prefix="/posts",         tags=["Posts"])
app.include_router(comments.router,     prefix="/comments",      tags=["Comments"])
app.include_router(courses.router,      prefix="/courses",       tags=["Courses"])
app.include_router(packages.router,     prefix="/packages",      tags=["Packages"])
app.include_router(modules.router,      prefix="/modules",       tags=["Modules"])
app.include_router(lessons.router,      prefix="/lessons",       tags=["Lessons"])
app.include_router(events.router,       prefix="/events",        tags=["Events"])
app.include_router(chats.router,        prefix="/chats",         tags=["Chats"])
app.include_router(notifications.router,prefix="/notifications", tags=["Notifications"])
app.include_router(badges.router,       prefix="/badges",        tags=["Badges"])
app.include_router(activities.router,   prefix="/activities",    tags=["Activities"])


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "DAIA Academy API"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
