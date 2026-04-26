from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from db.database import get_session
from db.models import Conversation, Message, User

router = APIRouter(prefix="/conversations", tags=["conversations"])


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    sources: list | None
    created_at: str


class ConversationOut(BaseModel):
    id: str
    title: str
    pinned: bool
    message_count: int
    created_at: str
    updated_at: str


class ConversationDetail(ConversationOut):
    messages: list[MessageOut]


class UpdateConversation(BaseModel):
    title: str | None = None
    pinned: bool | None = None


@router.get("", response_model=list[ConversationOut])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.pinned.desc(), Conversation.updated_at.desc())
    )
    convs = result.scalars().all()
    return [_conv_out(c) for c in convs]


@router.get("/{conv_id}", response_model=ConversationDetail)
async def get_conversation(
    conv_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Conversation)
        .where(Conversation.id == conv_id, Conversation.user_id == current_user.id)
        .options(selectinload(Conversation.messages))
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    out = _conv_out(conv)
    return ConversationDetail(
        **out.model_dump(),
        messages=[_msg_out(m) for m in conv.messages],
    )


@router.put("/{conv_id}", response_model=ConversationOut)
async def update_conversation(
    conv_id: str,
    body: UpdateConversation,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    conv = await _get_conv(conv_id, current_user.id, session)
    if body.title is not None:
        conv.title = body.title
    if body.pinned is not None:
        conv.pinned = body.pinned
    await session.commit()
    await session.refresh(conv)
    return _conv_out(conv)


@router.delete("/{conv_id}", status_code=204)
async def delete_conversation(
    conv_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    conv = await _get_conv(conv_id, current_user.id, session)
    await session.delete(conv)
    await session.commit()


async def _get_conv(conv_id: str, user_id: str, session: AsyncSession) -> Conversation:
    result = await session.execute(
        select(Conversation).where(Conversation.id == conv_id, Conversation.user_id == user_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


def _conv_out(c: Conversation) -> ConversationOut:
    return ConversationOut(
        id=c.id,
        title=c.title,
        pinned=c.pinned,
        message_count=c.message_count,
        created_at=c.created_at.isoformat(),
        updated_at=c.updated_at.isoformat(),
    )


def _msg_out(m: Message) -> MessageOut:
    return MessageOut(
        id=m.id,
        role=m.role.value,
        content=m.content,
        sources=m.sources,
        created_at=m.created_at.isoformat(),
    )
