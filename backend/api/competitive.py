"""
Competitive compare endpoint — streams a Claude analysis comparing internal product vs competitors.
"""

import json
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from db.database import get_session, async_session_maker
from db.models import Conversation, Message, MessageRole, User, gen_uuid
from agents.competitive_agent import stream_competitive_response

router = APIRouter(prefix="/competitive", tags=["competitive"])


class CompareRequest(BaseModel):
    query: str
    product_id: str | None = None
    competitor_ids: list[str] = []
    conversation_id: str | None = None


@router.post("/compare")
async def compare(
    body: CompareRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Get or create conversation
    conversation = None
    if body.conversation_id:
        result = await session.execute(
            select(Conversation).where(
                Conversation.id == body.conversation_id,
                Conversation.user_id == current_user.id,
            )
        )
        conversation = result.scalar_one_or_none()

    if not conversation:
        title = f"Competitive: {body.query[:50]}{'...' if len(body.query) > 50 else ''}"
        conversation = Conversation(
            id=gen_uuid(),
            user_id=current_user.id,
            title=title,
        )
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)

    # Load history
    history_result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(8)
    )
    history = [{"role": m.role.value, "content": m.content} for m in reversed(history_result.scalars().all())]

    # Save user message
    user_msg = Message(
        id=gen_uuid(),
        conversation_id=conversation.id,
        role=MessageRole.user,
        content=body.query,
    )
    session.add(user_msg)
    await session.commit()

    async def event_stream():
        yield _sse({"type": "conversation_id", "conversation_id": conversation.id})

        full_response = []
        sources = []
        tokens_used = 0

        async for event in stream_competitive_response(
            query=body.query,
            product_id=body.product_id,
            competitor_ids=body.competitor_ids,
            user_id=current_user.id,
            conversation_history=history,
        ):
            if event["type"] == "sources":
                sources = event["sources"]
                yield _sse(event)
            elif event["type"] == "text":
                full_response.append(event["delta"])
                yield _sse(event)
            elif event["type"] == "done":
                tokens_used = event["tokens_used"]
                yield _sse(event)

        # Persist
        async with async_session_maker() as save_session:
            assistant_msg = Message(
                id=gen_uuid(),
                conversation_id=conversation.id,
                role=MessageRole.assistant,
                content="".join(full_response),
                sources=sources,
                tokens_used=tokens_used,
            )
            save_session.add(assistant_msg)
            await save_session.execute(
                update(Conversation)
                .where(Conversation.id == conversation.id)
                .values(message_count=Conversation.message_count + 2, updated_at=datetime.utcnow())
            )
            await save_session.commit()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"
