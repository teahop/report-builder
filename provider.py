"""Thin model provider adapter — the only module that talks to an LLM client.

Interface: give me this schema back. Production may swap OpenAI for BastionGPT
without rewriting callers; BastionGPT may lack structured `response_format`,
in which case JSON-mode + parse/repair stays inside this file.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, TypeVar

import httpx

# Langfuse OpenAI drop-in: generations nest under @observe spans when keys are set.
# Without LANGFUSE_* env, the wrapper still talks to OpenAI; tracing is a no-op.
from langfuse.openai import OpenAI
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

DEFAULT_MODEL = "gpt-4o"
BASTION_MODEL = "bastiongpt-auto"
BASTION_BASE_URL = "https://api.bastiongpt.com"
BASTION_CHAT_PATH = "/v1/ChatCompletion"
BASTION_DEFAULT_MAX_TOKENS = 8192
BASTION_API_KEY_ENV_NAMES = (
    "BASTIONGPT_API_KEY",
    "BASTION_API_KEY",
    "BASTIONGPT_KEY",
)

# Sampling: extraction / ingest / entailment want correct answers (temp 0).
# Drafting stays at the prior API default — clinician-valued prose quality.
EXTRACT_TEMPERATURE = 0.0
INGEST_TEMPERATURE = 0.0
ENTAILMENT_TEMPERATURE = 0.0
DRAFT_TEMPERATURE = 1.0  # Named/configurable; A/B later — do not silently drop to 0.

MODEL_PRICES_PER_1K: dict[str, tuple[float, float]] = {
    "gpt-4o": (0.0025, 0.01),
    "gpt-4o-mini": (0.00015, 0.0006),
    "o3-mini": (0.0011, 0.0044),
}

_JSON_MODE_SUFFIX = (
    "\n\n---\n"
    "Provider adapter JSON mode: this runtime has no schema-constrained "
    "response_format. Reply with a single JSON object matching this schema. "
    "No markdown fences, no commentary.\n"
)


@dataclass(frozen=True, slots=True)
class StructuredResult:
    data: BaseModel
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    finish_reason: str | None = None
    provider: str = "openai"
    raw_text: str | None = None
    response_id: str | None = None


class BastionAccessError(RuntimeError):
    """BastionGPT rejected the key or the endpoint is not live."""


class BastionParseError(ValueError):
    """BastionGPT returned text that could not be parsed into the requested schema."""

    def __init__(
        self,
        message: str,
        *,
        raw_text: str,
        finish_reason: str | None = None,
        response_id: str | None = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
    ) -> None:
        super().__init__(message)
        self.raw_text = raw_text
        self.finish_reason = finish_reason
        self.response_id = response_id
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens


def compute_cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    prices = MODEL_PRICES_PER_1K.get(model, MODEL_PRICES_PER_1K[DEFAULT_MODEL])
    input_per_1k, output_per_1k = prices
    return (prompt_tokens / 1000 * input_per_1k) + (completion_tokens / 1000 * output_per_1k)


def bastion_api_key_from_env() -> str | None:
    for name in BASTION_API_KEY_ENV_NAMES:
        value = os.getenv(name)
        if value and value.strip():
            return value.strip()
    return None


def coerce_unregistered_extraction_predicates(payload: dict[str, Any]) -> dict[str, Any]:
    """Map unknown predicate strings onto the schema escape hatch.

    Bastion JSON-mode is not enum-constrained. The extract prompt already asks
    for ``__unregistered__`` + ``proposed_predicate``; this keeps that contract
    when the model names a new predicate directly.
    """

    from predicates import ExtractPredicateName, UNREGISTERED_PREDICATE

    allowed = {member.value for member in ExtractPredicateName}
    facts = payload.get("facts")
    if not isinstance(facts, list):
        return payload
    out = dict(payload)
    coerced: list[Any] = []
    for fact in facts:
        if not isinstance(fact, dict):
            coerced.append(fact)
            continue
        pred = fact.get("predicate")
        if isinstance(pred, str) and pred not in allowed:
            row = dict(fact)
            row["predicate"] = UNREGISTERED_PREDICATE
            row["proposed_predicate"] = (fact.get("proposed_predicate") or pred).strip()
            coerced.append(row)
        else:
            coerced.append(fact)
    out["facts"] = coerced
    return out


def parse_json_object(text: str) -> dict[str, Any]:
    """Best-effort object extraction for JSON-mode (fences / preamble)."""

    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object in model output")
    parsed = json.loads(stripped[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("JSON root is not an object")
    return parsed


def json_mode_system(system: str, schema: type[BaseModel]) -> str:
    return system + _JSON_MODE_SUFFIX + json.dumps(schema.model_json_schema())


def _usage_count(usage: dict[str, Any], *names: str) -> int:
    for name in names:
        value = usage.get(name)
        if value is not None:
            return int(value)
    return 0


class ModelProvider:
    """Structured-output adapter. Callers never import a vendor client directly."""

    def __init__(
        self,
        client: OpenAI | None = None,
        *,
        backend: str = "openai",
        http_client: Any | None = None,
        bastion_api_key: str | None = None,
    ) -> None:
        if backend not in {"openai", "bastion"}:
            raise ValueError(f"unsupported provider backend: {backend!r}")
        self._backend = backend
        self._http = http_client
        self._bastion_api_key = bastion_api_key
        if backend == "openai":
            self._client = client or OpenAI()
        else:
            self._client = client

    def complete_structured(
        self,
        *,
        model: str,
        system: str | None = None,
        user: str | None = None,
        schema: type[T],
        temperature: float | None = None,
        messages: list[dict] | None = None,
        max_tokens: int | None = None,
    ) -> StructuredResult:
        if messages is None:
            if system is None or user is None:
                raise ValueError("complete_structured requires system+user or messages")
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]
        if self._backend == "bastion":
            return self._complete_bastion_json(
                messages=messages,
                schema=schema,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        kwargs: dict = {
            "model": model,
            "messages": messages,
            "response_format": schema,
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        completion = self._client.chat.completions.parse(**kwargs)
        parsed = completion.choices[0].message.parsed
        if parsed is None:
            raise ValueError(f"Model returned no parseable {schema.__name__}")

        usage = completion.usage
        return StructuredResult(
            data=parsed,
            total_tokens=usage.total_tokens if usage else 0,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            provider="openai",
        )

    def _complete_bastion_json(
        self,
        *,
        messages: list[dict],
        schema: type[T],
        temperature: float | None,
        max_tokens: int | None,
    ) -> StructuredResult:
        key = self._bastion_api_key or bastion_api_key_from_env()
        if not key:
            raise BastionAccessError(
                "BastionGPT API key not found; expected "
                + ", ".join(BASTION_API_KEY_ENV_NAMES)
            )

        wrapped: list[dict] = []
        for index, message in enumerate(messages):
            if index == 0 and message.get("role") == "system":
                wrapped.append(
                    {
                        "role": "system",
                        "content": json_mode_system(str(message.get("content") or ""), schema),
                    }
                )
            else:
                wrapped.append(message)
        if not wrapped or wrapped[0].get("role") != "system":
            wrapped.insert(
                0,
                {"role": "system", "content": json_mode_system("", schema)},
            )

        payload = {
            "messages": wrapped,
            "max_tokens": max_tokens or BASTION_DEFAULT_MAX_TOKENS,
        }
        if temperature is not None:
            payload["temperature"] = temperature

        response = self._bastion_post(key, payload)
        if response.status_code == 401:
            raise BastionAccessError("BastionGPT returned 401 — key missing, invalid, or not live")
        if response.status_code >= 400:
            raise RuntimeError(
                f"BastionGPT HTTP {response.status_code}: {response.text[:300]}"
            )
        body = response.json()
        choice = (body.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        raw_text = message.get("content") or ""
        finish_reason = choice.get("finishReason") or choice.get("finish_reason")
        response_id = body.get("id")
        usage = body.get("usage") or {}
        prompt_tokens = _usage_count(usage, "promptTokens", "prompt_tokens")
        completion_tokens = _usage_count(usage, "completionTokens", "completion_tokens")
        total_tokens = _usage_count(usage, "totalTokens", "total_tokens") or (
            prompt_tokens + completion_tokens
        )
        if finish_reason == "content_filter":
            raise BastionParseError(
                "BastionGPT withheld content via safety filter",
                raw_text=raw_text,
                finish_reason=finish_reason,
                response_id=response_id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )
        try:
            from schemas import SourceExtraction

            obj = parse_json_object(raw_text)
            if schema is SourceExtraction:
                obj = coerce_unregistered_extraction_predicates(obj)
            parsed = schema.model_validate(obj)
        except (ValueError, ValidationError, json.JSONDecodeError) as exc:
            raise BastionParseError(
                f"BastionGPT JSON-mode parse failed for {schema.__name__}: {exc}",
                raw_text=raw_text,
                finish_reason=finish_reason,
                response_id=response_id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            ) from exc
        return StructuredResult(
            data=parsed,
            total_tokens=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            finish_reason=finish_reason,
            provider="bastion",
            raw_text=raw_text,
            response_id=response_id,
        )

    def _bastion_post(self, key: str, payload: dict[str, Any]) -> httpx.Response:
        url = f"{BASTION_BASE_URL}{BASTION_CHAT_PATH}"
        headers = {"key": key, "Content-Type": "application/json"}
        if self._http is not None:
            return self._http.post(url, headers=headers, json=payload, timeout=180.0)
        with httpx.Client(timeout=180.0) as client:
            return client.post(url, headers=headers, json=payload)
