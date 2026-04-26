"""
SSE-based chat endpoint.
POST /chat → streams text/event-stream with JSON events.
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
from agents.rag_agent import stream_rag_response

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    doc_ids: list[str] | None = None  # Optional: restrict to specific docs


@router.post("")
async def chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Get or create conversation
    if body.conversation_id:
        result = await session.execute(
            select(Conversation).where(
                Conversation.id == body.conversation_id,
                Conversation.user_id == current_user.id,
            )
        )
        conversation = result.scalar_one_or_none()
    else:
        conversation = None

    if not conversation:
        # Auto-title from first message (truncated)
        title = body.message[:60] + ("..." if len(body.message) > 60 else "")
        conversation = Conversation(
            id=gen_uuid(),
            user_id=current_user.id,
            title=title,
        )
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)

    # Load recent history
    history_result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(10)
    )
    history_msgs = list(reversed(history_result.scalars().all()))
    history = [{"role": m.role.value, "content": m.content} for m in history_msgs]

    # Save user message
    user_msg = Message(
        id=gen_uuid(),
        conversation_id=conversation.id,
        role=MessageRole.user,
        content=body.message,
    )
    session.add(user_msg)
    await session.commit()

    async def event_stream():
        # Send conversation_id first so client can track it
        yield _sse({"type": "conversation_id", "conversation_id": conversation.id})

        full_response = []
        sources = []
        tokens_used = 0

        async for event in stream_rag_response(
            query=body.message,
            conversation_history=history,
            doc_ids=body.doc_ids,
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

        # Persist assistant message in a new session (stream already closed)
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

            # Update conversation metadata
            await save_session.execute(
                update(Conversation)
                .where(Conversation.id == conversation.id)
                .values(
                    message_count=Conversation.message_count + 2,
                    updated_at=datetime.utcnow(),
                )
            )
            await save_session.commit()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"
