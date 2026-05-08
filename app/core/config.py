from __future__ import annotations

from typing import Self
from urllib.parse import quote_plus, urlparse

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _project_ref_from_supabase_url(url: str) -> str:
    host = (urlparse(url).hostname or "").strip().lower()
    if not host.endswith(".supabase.co"):
        msg = "SUPABASE_URL must look like https://<project-ref>.supabase.co"
        raise ValueError(msg)
    return host.split(".")[0]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Cognitive Dialogue Backend"
    env: str = "dev"
    log_level: str = "info"

    # Full async SQLAlchemy URL (preferred). If unset, built from Supabase fields below.
    database_url: str | None = None

    supabase_url: str | None = None
    supabase_key: str | None = None  # anon/publishable; not used for Postgres direct connection
    # Project Settings → Database → Database password (not the anon/publishable key).
    supabase_db_password: str | None = None

    llm_provider: str = "openai"
    llm_model: str = "gpt-4.1-mini"

    @model_validator(mode="after")
    def resolve_database_url(self) -> Self:
        if self.database_url:
            return self
        if self.supabase_url and self.supabase_db_password:
            ref = _project_ref_from_supabase_url(self.supabase_url)
            pwd = quote_plus(self.supabase_db_password)
            built = f"postgresql+asyncpg://postgres:{pwd}@db.{ref}.supabase.co:5432/postgres"
            object.__setattr__(self, "database_url", built)
            return self
        # Local dev default when neither DATABASE_URL nor Supabase password is set.
        object.__setattr__(
            self,
            "database_url",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/cognitive_dialogue",
        )
        return self


settings = Settings()

