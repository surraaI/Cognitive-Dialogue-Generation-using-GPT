from __future__ import annotations

from fastapi import APIRouter

from app.api.routes.chat import router as chat_router
from app.api.routes.memory import router as memory_router
from app.api.routes.mode import router as mode_router

api_router = APIRouter()
api_router.include_router(chat_router)
api_router.include_router(memory_router)
api_router.include_router(mode_router)

