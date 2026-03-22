from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.user import User
from models.event import Event, EventAttendee
from schemas.event import EventCreate, EventRead, AttendeeStatusUpdate
from utils.auth import get_current_user_id

router = APIRouter()


@router.get("/", response_model=list[EventRead])
async def list_events(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Event))
    return result.scalars().all()


@router.post("/", response_model=EventRead, status_code=201)
async def create_event(
    payload: EventCreate,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    event = Event(**payload.model_dump(), created_by=user.id)
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return event


@router.post("/{event_id}/rsvp", status_code=201)
async def rsvp_event(
    event_id: UUID,
    payload: AttendeeStatusUpdate,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    res = await db.execute(
        select(EventAttendee).where(EventAttendee.user_id == user.id, EventAttendee.event_id == event_id)
    )
    attendee = res.scalar_one_or_none()
    if attendee:
        attendee.status = payload.status
    else:
        db.add(EventAttendee(user_id=user.id, event_id=event_id, status=payload.status))
    return {"status": payload.status}
