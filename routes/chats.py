from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.user import User
from models.chat import Chat, ChatParticipant, Message
from schemas.chat import ChatCreate, ChatRead, MessageCreate, MessageRead
from utils.auth import get_current_user_id

router = APIRouter()


@router.post("/", response_model=ChatRead, status_code=201)
async def create_chat(
    payload: ChatCreate,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    chat = Chat(name=payload.name, chat_type=payload.chat_type, space_id=payload.space_id)
    db.add(chat)
    await db.flush()
    all_ids = set([user.id] + payload.participant_ids)
    for uid in all_ids:
        db.add(ChatParticipant(user_id=uid, chat_id=chat.id))
    await db.refresh(chat)
    return chat


@router.post("/{chat_id}/messages", response_model=MessageRead, status_code=201)
async def send_message(
    chat_id: UUID,
    payload: MessageCreate,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    membership = await db.execute(
        select(ChatParticipant).where(
            ChatParticipant.chat_id == chat_id, ChatParticipant.user_id == user.id
        )
    )
    if not membership.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a chat participant")
    msg = Message(**payload.model_dump(), chat_id=chat_id, sender_id=user.id)
    db.add(msg)
    await db.flush()
    await db.refresh(msg)
    return msg


@router.get("/{chat_id}/messages", response_model=list[MessageRead])
async def list_messages(
    chat_id: UUID,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    msgs = await db.execute(
        select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at)
    )
    return msgs.scalars().all()
