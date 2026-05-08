from __future__ import annotations

from app.cognitive.types import PromptContext


class LLMAdapter:
    """
    Temporary deterministic adapter so the rest of the cognitive pipeline
    can be implemented + tested without provider credentials.
    """

    async def generate(self, prompt: PromptContext) -> str:
        mode = prompt.mode
        tone = prompt.tone
        k = prompt.user_profile.get("knowledge_level", "beginner")
        attn = prompt.attention

        top_entities = [e["text"] for e in (attn.get("entities") or [])[:3]]
        top_phrases = [p["text"] for p in (attn.get("keyphrases") or [])[:3]]

        if float(attn.get("ambiguity_score") or 0.0) >= 0.6:
            return (
                f"({tone}, {mode}) I’m not fully sure what you mean yet. "
                "Can you clarify what outcome you want (e.g., design, code, debugging), "
                "and what part is most important?"
            )

        if mode == "concise":
            return (
                f"({tone}) Noted. Key focus: {', '.join(top_entities or top_phrases or ['your request'])}. "
                "Next: I’ll use recent turns + stored memory to answer consistently."
            )

        if mode == "socratic":
            focus = ", ".join(top_entities or top_phrases or ["the main idea"])
            return (
                f"({tone}) Before I answer directly: what do you already know about {focus}, "
                "and what would a good answer let you do next?"
            )

        # explanatory
        focus = ", ".join(top_entities or top_phrases or ["your topic"])
        if k == "advanced":
            return f"({tone}) I’ll keep it technical. Focus: {focus}. What constraints (latency, storage, eval) matter most?"
        return f"({tone}) I’ll explain step-by-step. Focus: {focus}. Tell me your current goal and I’ll adapt the depth."

