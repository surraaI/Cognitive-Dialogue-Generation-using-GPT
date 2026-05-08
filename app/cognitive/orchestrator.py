from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.cognitive.attention import extract_attention
from app.cognitive.llm_adapter import LLMAdapter
from app.cognitive.memory import MemoryManager
from app.cognitive.prompt_builder import PromptBuilder
from app.cognitive.types import AttentionSignals, PromptContext, UserProfile
from app.db.models.user import User
from app.db.models.user_memory_item import UserMemoryItem


class CognitiveOrchestrator:
    def __init__(
        self,
        *,
        memory_manager: MemoryManager | None = None,
        prompt_builder: PromptBuilder | None = None,
        llm: LLMAdapter | None = None,
    ):
        self.memory_manager = memory_manager or MemoryManager()
        self.prompt_builder = prompt_builder or PromptBuilder()
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

        # Minimal memory suggestions (not auto-writing yet).
        memory_suggestions: list[dict] = []
        if mode and mode != user.default_mode:
            memory_suggestions.append({"key": "pref:mode", "action": "suggest_update", "confidence": 0.6})
        if tone and tone != user.tone:
            memory_suggestions.append({"key": "pref:tone", "action": "suggest_update", "confidence": 0.6})

        return assistant_text, attention, memory_suggestions, prompt

