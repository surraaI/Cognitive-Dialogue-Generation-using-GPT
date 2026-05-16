from __future__ import annotations

from app.cognitive.system_prompt import (
    get_few_shot_examples,
    get_system_role_for_mode,
    format_few_shot_for_prompt,
)
from app.cognitive.types import AttentionSignals, MemoryContext, PromptContext, UserProfile


class PromptBuilder:
    def build(
        self,
        *,
        user_profile: UserProfile,
        mode: str,
        tone: str,
        user_message: str,
        attention: AttentionSignals,
        memory: MemoryContext,
    ) -> PromptContext:
        # Centralize system role selection in system_prompt
        system_role = get_system_role_for_mode(mode)

        memory_payload = {
            "short_term": {
                "summary": memory.short_term.summary,
                "recent_turns": memory.short_term.recent_turns,
            },
            "long_term": [
                {
                    "key": item.key,
                    "value": item.value,
                    "confidence": item.confidence,
                    "importance": item.importance,
                }
                for item in memory.long_term
            ],
        }

        # Append formatted few-shot examples (kept brief) when in Socratic mode
        if mode.lower() == "socratic":
            system_role = system_role + "\n\n" + format_few_shot_for_prompt(limit=2)

        return PromptContext(
            system_role=system_role,
            mode=mode,
            tone=tone,
            user_profile={
                "user_id": user_profile.user_id,
                "knowledge_level": user_profile.knowledge_level,
                "default_mode": user_profile.default_mode,
                "tone": user_profile.tone,
                "preferences": user_profile.preferences,
            },
            attention={
                "entities": attention.entities,
                "keyphrases": attention.keyphrases,
                "intent": attention.intent,
                "ambiguity_score": attention.ambiguity_score,
            },
            memory=memory_payload,
            user_message=user_message,
        )

