from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


DialogueMode = Literal["explanatory", "socratic", "concise"]
Tone = Literal["formal", "friendly", "instructional"]


@dataclass(frozen=True)
class AttentionSignals:
    entities: list[dict] = field(default_factory=list)
    keyphrases: list[dict] = field(default_factory=list)
    intent: str | None = None
    ambiguity_score: float = 0.0


@dataclass(frozen=True)
class UserProfile:
    user_id: str
    knowledge_level: str = "beginner"
    default_mode: str = "explanatory"
    tone: str = "friendly"
    preferences: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ShortTermMemory:
    recent_turns: list[dict]
    summary: str | None = None


@dataclass(frozen=True)
class LongTermMemoryItem:
    key: str
    value: dict
    confidence: float
    importance: float
    updated_at: datetime | None = None


@dataclass(frozen=True)
class MemoryContext:
    short_term: ShortTermMemory
    long_term: list[LongTermMemoryItem]


@dataclass(frozen=True)
class PromptContext:
    system_role: str
    mode: str
    tone: str
    user_profile: dict
    attention: dict
    memory: dict
    user_message: str

