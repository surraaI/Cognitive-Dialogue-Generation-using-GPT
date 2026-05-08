from __future__ import annotations

from app.cognitive.types import PromptContext


class Summarizer:
    """
    Simple summarizer placeholder. Later this can call the LLM with a dedicated
    summarization prompt and store the result in conversation_state.summary.
    """

    def summarize_recent_turns(self, recent_turns: list[dict], *, max_chars: int = 600) -> str:
        # Naive extractive summary: keep last few turns and truncate.
        chunks: list[str] = []
        for t in recent_turns[-6:]:
            role = t.get("role", "unknown")
            content = (t.get("content") or "").strip().replace("\n", " ")
            if content:
                chunks.append(f"{role}: {content}")
        out = " | ".join(chunks)
        if len(out) > max_chars:
            return out[: max_chars - 3] + "..."
        return out

