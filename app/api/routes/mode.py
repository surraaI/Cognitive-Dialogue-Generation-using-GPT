from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.conversation import Conversation
from app.db.models.user import User
from app.db.session import get_db_session

router = APIRouter(tags=["mode"])


class ModeRequest(BaseModel):
    user_id: uuid.UUID
    conversation_id: uuid.UUID | None = None
    mode: str = Field(..., pattern="^(explanatory|socratic|concise)$")
    tone: str | None = Field(default=None, pattern="^(formal|friendly|instructional)$")


class ModeResponse(BaseModel):
    applied_to: str  # conversation | user_default
    mode: str
    tone: str | None = None


@router.post("/mode", response_model=ModeResponse)
async def set_mode(payload: ModeRequest, db: AsyncSession = Depends(get_db_session)) -> ModeResponse:
    user = await db.get(User, payload.user_id)
    if user is None:
        user = User(id=payload.user_id)
        db.add(user)
        await db.flush()

    if payload.conversation_id is not None:
        conv = await db.get(Conversation, payload.conversation_id)
        if conv is None:
            conv = Conversation(user_id=user.id)
            db.add(conv)
            await db.flush()
        conv.mode = payload.mode
        if payload.tone:
            conv.tone = payload.tone
        conv.updated_at = datetime.utcnow()
        await db.commit()
        return ModeResponse(applied_to="conversation", mode=conv.mode, tone=conv.tone)

    user.default_mode = payload.mode
    if payload.tone:
        user.tone = payload.tone
    await db.commit()
    return ModeResponse(applied_to="user_default", mode=user.default_mode, tone=user.tone)

