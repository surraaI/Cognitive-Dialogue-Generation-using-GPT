from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.models.user_memory_item import UserMemoryItem
from app.db.session import get_db_session

router = APIRouter(tags=["memory"])


class MemoryItemOut(BaseModel):
    key: str
    value: dict
    confidence: float
    importance: float


class MemoryResponse(BaseModel):
    user_id: uuid.UUID
    profile: dict
    memory_items: list[MemoryItemOut]


@router.get("/memory", response_model=MemoryResponse)
async def get_memory(
    user_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db_session),
) -> MemoryResponse:
    user = await db.get(User, user_id)
    if user is None:
        # For now: empty profile if user not created yet.
        return MemoryResponse(user_id=user_id, profile={}, memory_items=[])

    items = (
        await db.execute(
            select(UserMemoryItem)
            .where(UserMemoryItem.user_id == user_id)
            .order_by(UserMemoryItem.importance.desc(), UserMemoryItem.updated_at.desc())
            .limit(200)
        )
    ).scalars().all()

    return MemoryResponse(
        user_id=user_id,
        profile={
            "knowledge_level": user.knowledge_level,
            "default_mode": user.default_mode,
            "tone": user.tone,
        },
        memory_items=[
            MemoryItemOut(key=i.key, value=i.value, confidence=i.confidence, importance=i.importance) for i in items
        ],
    )

