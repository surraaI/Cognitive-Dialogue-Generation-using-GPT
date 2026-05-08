from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cognitive.types import LongTermMemoryItem, MemoryContext, ShortTermMemory
from app.db.models.message import Message
from app.db.models.user_memory_item import UserMemoryItem


class MemoryManager:
    def __init__(self, *, recent_turn_limit: int = 16, long_term_limit: int = 50):
        self.recent_turn_limit = recent_turn_limit
        self.long_term_limit = long_term_limit

    async def build_context(self, *, db: AsyncSession, conversation_id, user_id) -> MemoryContext:
        recent = (
            await db.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.desc())
                .limit(self.recent_turn_limit)
            )
        ).scalars().all()
        recent_turns = [
            {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()} for m in reversed(recent)
        ]

        ltm = (
            await db.execute(
                select(UserMemoryItem)
                .where(UserMemoryItem.user_id == user_id)
                .order_by(UserMemoryItem.importance.desc(), UserMemoryItem.updated_at.desc())
                .limit(self.long_term_limit)
            )
        ).scalars().all()
        long_term = [
            LongTermMemoryItem(
                key=i.key,
                value=i.value,
                confidence=float(i.confidence),
                importance=float(i.importance),
                updated_at=i.updated_at,
            )
            for i in ltm
        ]

        # Summary is a later enhancement (conversation_state table). Keep None for now.
        return MemoryContext(short_term=ShortTermMemory(recent_turns=recent_turns, summary=None), long_term=long_term)

