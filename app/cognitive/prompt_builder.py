from __future__ import annotations

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
        system_role = (
            "You are a cognitive science tutor and dialogue assistant. "
            "Adapt explanations to the user's knowledge level and preferred tone. "
            "Use short-term memory (recent turns), long-term memory (user profile + stored facts), "
            "and attention signals (entities/keyphrases/ambiguity) to stay coherent. "
            "Use Socratic questioning when mode is socratic or when clarification is needed. "
            "Do not invent facts; prefer concise, educational explanations with examples."
        )

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

