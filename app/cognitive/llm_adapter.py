from __future__ import annotations

import asyncio
import json
import logging
import re
from urllib import error as urlerror
from urllib import request as urlrequest

from app.core.config import settings
from app.cognitive.types import PromptContext
from app.cognitive.system_prompt import build_generation_instruction

logger = logging.getLogger(__name__)


class LLMAdapter:
    """LLM adapter that prioritizes external providers over local fallback."""

    async def generate(self, prompt: PromptContext) -> str:
        provider = (settings.llm_provider or "openai").strip().lower()
        if provider == "openai" and settings.openai_api_key:
            try:
                raw = await self._generate_openai(prompt)
                return _postprocess_model_text(raw)
            except Exception as exc:
                logger.warning("OpenAI generation failed, using fallback: %s", exc)
        elif provider == "openai":
            logger.warning("OpenAI selected but OPENAI_API_KEY is not set")

        if provider == "gemini" and settings.gemini_api_key:
            try:
                raw = await self._generate_gemini(prompt)
                return _postprocess_model_text(raw)
            except Exception as exc:
                logger.warning("Gemini generation failed, using fallback: %s", exc)
        elif provider == "gemini":
            logger.warning("Gemini selected but GEMINI_API_KEY is not set")

        return self._generate_fallback(prompt)

    async def _generate_openai(self, prompt: PromptContext) -> str:
        payload = {
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": prompt.system_role},
                {
                    "role": "user",
                    "content": build_generation_instruction(prompt),
                },
            ],
            "temperature": 0.5,
        }
        base = settings.openai_base_url.rstrip("/")
        endpoint = f"{base}/chat/completions"
        req = urlrequest.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.openai_api_key}",
            },
            method="POST",
        )

        def _send() -> str:
            try:
                with urlrequest.urlopen(req, timeout=settings.openai_timeout_seconds) as resp:
                    raw = resp.read().decode("utf-8")
            except urlerror.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"OpenAI request failed: HTTP {exc.code}: {body}") from exc
            except urlerror.URLError as exc:
                raise RuntimeError(f"OpenAI network error: {exc}") from exc

            data = json.loads(raw)
            choices = data.get("choices") or []
            if not choices:
                raise RuntimeError("OpenAI response missing choices")
            message = choices[0].get("message") or {}
            content = message.get("content")
            if isinstance(content, list):
                parts = [p.get("text", "") for p in content if isinstance(p, dict)]
                text = "\n".join([p for p in parts if p]).strip()
            else:
                text = (content or "").strip()
            if not text:
                raise RuntimeError("OpenAI response content is empty")
            return text

        return await asyncio.to_thread(_send)

    async def _generate_gemini(self, prompt: PromptContext) -> str:
        configured = (settings.llm_model or "gemini-1.5-flash").strip()
        candidates = _gemini_model_candidates(configured)

        last_error: Exception | None = None
        for model_name in candidates:
            try:
                return await asyncio.to_thread(self._send_gemini_request, model_name, prompt)
            except RuntimeError as exc:
                last_error = exc
                if "HTTP 404" in str(exc):
                    logger.warning("Gemini model '%s' not available; trying next candidate", model_name)
                    continue
                raise

        raise RuntimeError(f"Gemini request failed for all model candidates: {last_error}")

    def _send_gemini_request(self, model_name: str, prompt: PromptContext) -> str:
        base = settings.gemini_base_url.rstrip("/")
        endpoint = f"{base}/models/{model_name}:generateContent?key={settings.gemini_api_key}"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": build_generation_instruction(prompt)}]}],
            "systemInstruction": {"parts": [{"text": prompt.system_role}]},
            "generationConfig": {"temperature": 0.5},
        }
        req = urlrequest.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlrequest.urlopen(req, timeout=settings.gemini_timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
        except urlerror.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Gemini request failed: HTTP {exc.code}: {body}") from exc
        except urlerror.URLError as exc:
            raise RuntimeError(f"Gemini network error: {exc}") from exc

        # Visibility-first debug output for terminal sessions.
        print(f"Gemini raw response: {raw}", flush=True)
        logger.warning("Gemini raw response logged to terminal")

        data = json.loads(raw)
        candidates = data.get("candidates") or []
        if not candidates:
            raise RuntimeError("Gemini response missing candidates")
        content = (candidates[0] or {}).get("content") or {}
        parts = content.get("parts") or []
        text_parts = [p.get("text", "") for p in parts if isinstance(p, dict)]
        text = "\n".join([p for p in text_parts if p]).strip()
        if not text:
            raise RuntimeError("Gemini response content is empty")
        return text

    def _generate_fallback(self, prompt: PromptContext) -> str:
        provider = (settings.llm_provider or "openai").strip().lower()
        return (
            "I cannot reach the configured language model right now, so I cannot provide a reliable generated response. "
            f"Current provider is '{provider}'. Please verify API key, quota, and network access, then try again."
        )





def _gemini_model_candidates(configured_model: str) -> list[str]:
    model = configured_model.strip()
    fallbacks = [
        model,
        "gemini-2.5-flash"
    ]
    seen: set[str] = set()
    ordered: list[str] = []
    for m in fallbacks:
        key = m.strip()
        if key and key not in seen:
            seen.add(key)
            ordered.append(key)
    return ordered


def _postprocess_model_text(raw_text: str) -> str:
    # For plain text responses (Socratic mode), return as-is
    payload = _try_parse_json(raw_text)
    if not payload:
        return raw_text.strip()

    # For JSON responses (other modes), extract and format
    direct_answer = str(payload.get("direct_answer") or "").strip()
    worked_example = str(payload.get("worked_example") or "").strip()
    check_question = str(payload.get("check_question") or "").strip()

    parts: list[str] = []
    if direct_answer:
        parts.append(direct_answer)
    if worked_example:
        parts.append(f"Example: {worked_example}")
    if check_question:
        parts.append(f"Check: {check_question}")

    return "\n\n".join(parts).strip() or raw_text.strip()


def _try_parse_json(raw_text: str) -> dict | None:
    text = raw_text.strip()
    try:
        loaded = json.loads(text)
        return loaded if isinstance(loaded, dict) else None
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        loaded = json.loads(match.group(0))
        return loaded if isinstance(loaded, dict) else None
    except json.JSONDecodeError:
        return None

