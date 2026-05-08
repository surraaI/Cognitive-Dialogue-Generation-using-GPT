from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cognitive.attention import extract_attention
from app.cognitive.llm_adapter import LLMAdapter
from app.cognitive.memory import MemoryManager
from app.cognitive.prompt_builder import PromptBuilder
from app.cognitive.summarizer import Summarizer
from app.cognitive.types import AttentionSignals, PromptContext, UserProfile
from app.db.models.conversation_state import ConversationState
from app.db.models.user import User
from app.db.models.user_memory_item import UserMemoryItem


class CognitiveOrchestrator:
    def __init__(
        self,
        *,
        memory_manager: MemoryManager | None = None,
        prompt_builder: PromptBuilder | None = None,
        summarizer: Summarizer | None = None,
        llm: LLMAdapter | None = None,
    ):
        self.memory_manager = memory_manager or MemoryManager()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.summarizer = summarizer or Summarizer()
        self.llm = llm or LLMAdapter()

    async def run(
        self,
        *,
        db: AsyncSession,
        user: User,
        conversation_id: uuid.UUID,
        user_message: str,
        mode: str,
        tone: str,
    ) -> tuple[str, AttentionSignals, list[dict], PromptContext]:
        # Keep conversation state updated (rolling summary + turn count).
        state = await db.get(ConversationState, conversation_id)
        if state is None:
            state = ConversationState(conversation_id=conversation_id, working_memory={})
            db.add(state)
            await db.flush()

        attention = extract_attention(user_message)
        memory = await self.memory_manager.build_context(db=db, conversation_id=conversation_id, user_id=user.id)

        # Basic preferences from LTM (pref:*)
        preferences: dict = {}
        for item in memory.long_term:
            if item.key.startswith("pref:"):
                preferences[item.key.removeprefix("pref:")] = item.value

        profile = UserProfile(
            user_id=str(user.id),
            knowledge_level=user.knowledge_level,
            default_mode=user.default_mode,
            tone=user.tone,
            preferences=preferences,
        )

        prompt = self.prompt_builder.build(
            user_profile=profile,
            mode=mode,
            tone=tone,
            user_message=user_message,
            attention=attention,
            memory=memory,
        )

        assistant_text = await self.llm.generate(prompt)

        # Increment turn count + refresh summary after enough turns.
        state.turn_count = int(state.turn_count or 0) + 1
        if state.turn_count % 6 == 0:
            state.summary = self.summarizer.summarize_recent_turns(memory.short_term.recent_turns)
            state.summary_updated_at = datetime.utcnow()

        # Long-term memory writebacks: persist preferences for consistency.
        memory_suggestions: list[dict] = []
        await _upsert_pref(db=db, user_id=user.id, key="pref:mode", value={"mode": mode}, source="inferred")
        await _upsert_pref(db=db, user_id=user.id, key="pref:tone", value={"tone": tone}, source="inferred")
        memory_suggestions.append({"key": "pref:mode", "action": "upsert", "confidence": 0.8})
        memory_suggestions.append({"key": "pref:tone", "action": "upsert", "confidence": 0.8})

        return assistant_text, attention, memory_suggestions, prompt


async def _upsert_pref(*, db: AsyncSession, user_id, key: str, value: dict, source: str) -> None:
    existing = (
        await db.execute(select(UserMemoryItem).where(UserMemoryItem.user_id == user_id, UserMemoryItem.key == key))
    ).scalars().first()

    now = datetime.utcnow()
    if existing is None:
        db.add(
            UserMemoryItem(
                user_id=user_id,
                key=key,
                value=value,
                source=source,
                confidence=0.8,
                importance=0.7,
                created_at=now,
                updated_at=now,
            )
        )
        return

    existing.value = value
    existing.source = source
    existing.updated_at = now

