from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Cognitive Dialogue Backend"
    env: str = "dev"
    log_level: str = "info"

    # Default keeps imports working without a local `.env`.
    # Override via `DATABASE_URL` when running migrations / app.
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cognitive_dialogue"

    llm_provider: str = "openai"
    llm_model: str = "gpt-4.1-mini"


settings = Settings()

