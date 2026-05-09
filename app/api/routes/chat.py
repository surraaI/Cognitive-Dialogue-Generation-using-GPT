from __future__ import annotations

import re
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.cognitive.attention import extract_attention
from app.cognitive.llm_adapter import LLMAdapter
from app.cognitive.orchestrator import CognitiveOrchestrator
from app.cognitive.prompt_builder import PromptBuilder
from app.cognitive.types import MemoryContext, ShortTermMemory, UserProfile
from app.db.models.conversation import Conversation
from app.db.models.message import Message
from app.db.models.user import User
from app.db.session import get_db_session

router = APIRouter(tags=["chat"])

_FALLBACK_CONVERSATIONS: dict[uuid.UUID, dict] = {}
_FALLBACK_MESSAGES: dict[uuid.UUID, list[dict]] = {}
_FALLBACK_USER_PREFS: dict[uuid.UUID, dict] = {}


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
    try:
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

        # Cognitive pipeline (deterministic LLM adapter for now).
        orchestrator = CognitiveOrchestrator()
        assistant_text, attention, memory_suggestions, _prompt = await orchestrator.run(
            db=db,
            user=user,
            conversation_id=conversation.id,
            user_message=payload.message,
            mode=(payload.mode or conversation.mode),
            tone=(payload.tone or conversation.tone),
        )

        db.add(
            Message(
                conversation_id=conversation.id,
                role="assistant",
                content=assistant_text,
                created_at=datetime.utcnow(),
                metadata_={"cognitive_pipeline": True},
            )
        )

        # Update conversation mode/tone if supplied.
        if payload.mode:
            conversation.mode = payload.mode
        if payload.tone:
            conversation.tone = payload.tone
        conversation.updated_at = datetime.utcnow()

        await db.commit()

        return ChatResponse(
            conversation_id=conversation.id,
            assistant_message=assistant_text,
            mode=conversation.mode,
            tone=conversation.tone,
            attention=AttentionSignals(
                entities=attention.entities,
                keyphrases=attention.keyphrases,
                ambiguity_score=attention.ambiguity_score,
            ),
            memory_updates=[MemoryUpdate(**m) for m in memory_suggestions],
        )
    except (SQLAlchemyError, OSError):
        return await _chat_without_db(payload)


async def _chat_without_db(payload: ChatRequest) -> ChatResponse:
    user_prefs = _FALLBACK_USER_PREFS.setdefault(
        payload.user_id, {"default_mode": "explanatory", "tone": "friendly", "knowledge_level": "beginner"}
    )

    if payload.conversation_id and payload.conversation_id in _FALLBACK_CONVERSATIONS:
        conversation_id = payload.conversation_id
        convo = _FALLBACK_CONVERSATIONS[conversation_id]
    else:
        conversation_id = payload.conversation_id or uuid.uuid4()
        convo = {
            "user_id": payload.user_id,
            "mode": payload.mode or user_prefs["default_mode"],
            "tone": payload.tone or user_prefs["tone"],
        }
        _FALLBACK_CONVERSATIONS[conversation_id] = convo

    mode = payload.mode or convo["mode"]
    tone = payload.tone or convo["tone"]
    convo["mode"] = mode
    convo["tone"] = tone
    _apply_profile_updates(user_prefs, payload.message)

    turns = _FALLBACK_MESSAGES.setdefault(conversation_id, [])
    turns.append({"role": "user", "content": payload.message, "created_at": datetime.utcnow().isoformat()})

    attention = extract_attention(payload.message)
    memory = MemoryContext(short_term=ShortTermMemory(recent_turns=turns[-16:], summary=None), long_term=[])
    prompt = PromptBuilder().build(
        user_profile=UserProfile(
            user_id=str(payload.user_id),
            knowledge_level=user_prefs["knowledge_level"],
            default_mode=user_prefs["default_mode"],
            tone=user_prefs["tone"],
            preferences={
                "mode": mode,
                "tone": tone,
                "display_name": user_prefs.get("display_name"),
            },
        ),
        mode=mode,
        tone=tone,
        user_message=payload.message,
        attention=attention,
        memory=memory,
    )
    assistant_text = await LLMAdapter().generate(prompt)

    turns.append({"role": "assistant", "content": assistant_text, "created_at": datetime.utcnow().isoformat()})
    user_prefs["default_mode"] = mode
    user_prefs["tone"] = tone

    memory_updates = [
        MemoryUpdate(key="pref:mode", action="upsert", confidence=0.8),
        MemoryUpdate(key="pref:tone", action="upsert", confidence=0.8),
    ]
    return ChatResponse(
        conversation_id=conversation_id,
        assistant_message=assistant_text,
        mode=mode,
        tone=tone,
        attention=AttentionSignals(
            entities=attention.entities,
            keyphrases=attention.keyphrases,
            ambiguity_score=attention.ambiguity_score,
        ),
        memory_updates=memory_updates,
    )


def _apply_profile_updates(user_prefs: dict, message: str) -> None:
    text = message.strip()
    m = re.search(r"\bmy name is\s+([A-Za-z][A-Za-z\-']{0,50})\b", text, flags=re.IGNORECASE)
    if m:
        user_prefs["display_name"] = m.group(1)

