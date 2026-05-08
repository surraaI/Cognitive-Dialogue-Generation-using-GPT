from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.conversation import Conversation
from app.db.models.message import Message
from app.db.models.user import User
from app.db.session import get_db_session

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    user_id: uuid.UUID
    conversation_id: uuid.UUID | None = None
    message: str = Field(min_length=1)
    mode: str | None = None
    tone: str | None = None
    metadata: dict = Field(default_factory=dict)


class AttentionSignals(BaseModel):
    entities: list[dict] = Field(default_factory=list)
    keyphrases: list[dict] = Field(default_factory=list)
    ambiguity_score: float = 0.0


class MemoryUpdate(BaseModel):
    key: str
    action: str
    confidence: float = 0.5


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    assistant_message: str
    mode: str
    tone: str
    attention: AttentionSignals = Field(default_factory=AttentionSignals)
    memory_updates: list[MemoryUpdate] = Field(default_factory=list)


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, db: AsyncSession = Depends(get_db_session)) -> ChatResponse:
    # Ensure user exists (minimal bootstrap for terminal-first usage).
    user = await db.get(User, payload.user_id)
    if user is None:
        user = User(id=payload.user_id)
        db.add(user)
        await db.flush()

    # Ensure conversation exists.
    conversation: Conversation | None = None
    if payload.conversation_id is not None:
        conversation = await db.get(Conversation, payload.conversation_id)

    if conversation is None:
        conversation = Conversation(
            user_id=user.id,
            mode=payload.mode or user.default_mode,
            tone=payload.tone or user.tone,
        )
        db.add(conversation)
        await db.flush()

    # Persist user message.
    db.add(
        Message(
            conversation_id=conversation.id,
            role="user",
            content=payload.message,
            created_at=datetime.utcnow(),
            metadata_=payload.metadata,
        )
    )

    # Placeholder “cognitive pipeline” response (LLM wiring comes next commit).
    assistant_text = "LLM not wired yet. Next commit will add cognitive modules + prompt builder."

    db.add(
        Message(
            conversation_id=conversation.id,
            role="assistant",
            content=assistant_text,
            created_at=datetime.utcnow(),
            metadata_={"placeholder": True},
        )
    )

    # Update conversation mode/tone if supplied.
    if payload.mode:
        conversation.mode = payload.mode
    if payload.tone:
        conversation.tone = payload.tone
    conversation.updated_at = datetime.utcnow()

    await db.commit()

    # Minimal attention placeholder: echo nothing for now.
    return ChatResponse(
        conversation_id=conversation.id,
        assistant_message=assistant_text,
        mode=conversation.mode,
        tone=conversation.tone,
    )

