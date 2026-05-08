from __future__ import annotations

from fastapi import FastAPI

from app.core.config import settings
from app.api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    app.include_router(api_router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

