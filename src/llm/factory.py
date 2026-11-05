"""Sarvam Token Factory model factory (OpenAI-compatible /v2/chat/completions)."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from src.core.config import settings

try:
    from langchain_openai import ChatOpenAI
except Exception:  # pragma: no cover - optional dependency
    ChatOpenAI = None  # type: ignore


def get_llm_api_key() -> str | None:
    return (
        settings.llm_api_key
        or settings.sarvam_api_key
        or os.environ.get("SARVAM_API_KEY")
        or os.environ.get("AGENTIC_BI_LLM_API_KEY")
    )


def llm_enabled() -> bool:
    return bool(get_llm_api_key()) and settings.engine.lower() != "legacy" and ChatOpenAI is not None



@lru_cache(maxsize=8)
def _cached_model(model: str, temperature: float, max_tokens: int, timeout_s: int, max_retries: int, reasoning: str | None):
    api_key = get_llm_api_key()
    if not api_key:
        raise RuntimeError("Sarvam API key not configured (SARVAM_API_KEY / AGENTIC_BI_LLM_API_KEY).")
    if ChatOpenAI is None:
        raise RuntimeError("langchain-openai is not installed.")
    kwargs: dict[str, Any] = {}
    if reasoning:
        # Sarvam accepts OpenAI-compatible clients; reasoning controls are passed via extra_body.
        kwargs["extra_body"] = {"reasoning_effort": reasoning}
    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=settings.llm_base_url,
        temperature=temperature,
        timeout=timeout_s,
        max_retries=max_retries,
        max_tokens=max_tokens,
        **kwargs,
    )


def get_chat_model(task: str = "default"):
    task = (task or "default").lower()
    model = settings.llm_model
    mapping = {
        "router": settings.llm_model_router,
        "grounder": settings.llm_model_grounder,
        "sql": settings.llm_model_sql,
        "repair": settings.llm_model_repair,
        "narrative": settings.llm_model_narrative,
    }
    model = mapping.get(task) or model
    reasoning = settings.llm_reasoning_effort
    # glm5.3-flash reasoning can't be turned off; avoid forcing "none".
    if model and "glm5.3" in model and reasoning == "none":
        reasoning = None
    return _cached_model(
        model=model,
        temperature=float(settings.llm_temperature),
        max_tokens=int(settings.llm_max_tokens),
        timeout_s=int(settings.llm_timeout_s),
        max_retries=int(settings.llm_max_retries),
        reasoning=reasoning,
    )
