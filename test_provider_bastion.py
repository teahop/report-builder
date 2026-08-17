"""Offline tests for BastionGPT JSON-mode inside the provider adapter."""

from __future__ import annotations

import json

import pytest

from provider import (
    BASTION_BASE_URL,
    BASTION_CHAT_PATH,
    BASTION_MODEL,
    BastionAccessError,
    BastionParseError,
    ModelProvider,
    coerce_unregistered_extraction_predicates,
    json_mode_system,
    parse_json_object,
)
from schemas import SourceExtraction


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict | str) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = payload if isinstance(payload, str) else json.dumps(payload)

    def json(self) -> dict:
        assert isinstance(self._payload, dict)
        return self._payload


class _FakeHttp:
    def __init__(self, response: _FakeResponse) -> None:
        self.response = response
        self.calls: list[dict] = []

    def post(self, url, headers, json, timeout=None):  # noqa: A002
        self.calls.append(
            {"url": url, "headers": headers, "json": json, "timeout": timeout}
        )
        return self.response


def test_parse_json_object_strips_fences_and_preamble() -> None:
    text = 'Sure.\n```json\n{"facts": []}\n```\n'
    assert parse_json_object(text) == {"facts": []}


def test_json_mode_system_keeps_product_prompt_as_prefix() -> None:
    wrapped = json_mode_system("PRODUCT PROMPT", SourceExtraction)
    assert wrapped.startswith("PRODUCT PROMPT")
    assert "Provider adapter JSON mode" in wrapped
    assert "SourceExtraction" in wrapped or "facts" in wrapped


def test_bastion_backend_parses_chat_completion_json() -> None:
    extraction = {
        "facts": [
            {
                "subject": "child",
                "predicate": "legal_name",
                "value": "Emma Rose Callahan",
                "value_text": "Student Name: Emma Rose Callahan",
                "life_stage": "current",
                "confidence": "stated",
            }
        ]
    }
    http = _FakeHttp(
        _FakeResponse(
            200,
            {
                "id": "fake-id",
                "choices": [
                    {
                        "finishReason": "stop",
                        "message": {"content": json.dumps(extraction)},
                    }
                ],
                "usage": {
                    "promptTokens": 11,
                    "completionTokens": 7,
                    "totalTokens": 18,
                },
            },
        )
    )
    provider = ModelProvider(
        backend="bastion",
        http_client=http,
        bastion_api_key="test-key",
    )
    result = provider.complete_structured(
        model=BASTION_MODEL,
        system="extract facts",
        user="source text",
        schema=SourceExtraction,
        temperature=0.0,
        max_tokens=64,
    )
    assert result.provider == "bastion"
    assert result.total_tokens == 18
    assert result.finish_reason == "stop"
    assert isinstance(result.data, SourceExtraction)
    assert result.data.facts[0].predicate.value == "legal_name"
    assert http.calls[0]["url"] == f"{BASTION_BASE_URL}{BASTION_CHAT_PATH}"
    assert http.calls[0]["headers"]["key"] == "test-key"
    sent = http.calls[0]["json"]
    assert sent["max_tokens"] == 64
    assert sent["temperature"] == 0.0
    assert sent["messages"][0]["role"] == "system"
    assert sent["messages"][0]["content"].startswith("extract facts")
    assert "model" not in sent


def test_bastion_401_is_access_error() -> None:
    http = _FakeHttp(_FakeResponse(401, {"statusCode": 401, "message": "denied"}))
    provider = ModelProvider(
        backend="bastion",
        http_client=http,
        bastion_api_key="bad-key",
    )
    with pytest.raises(BastionAccessError, match="401"):
        provider.complete_structured(
            model=BASTION_MODEL,
            system="s",
            user="u",
            schema=SourceExtraction,
        )


def test_bastion_non_json_raises_parse_error_with_raw_text() -> None:
    http = _FakeHttp(
        _FakeResponse(
            200,
            {
                "choices": [
                    {
                        "finishReason": "stop",
                        "message": {"content": "I cannot emit JSON."},
                    }
                ],
                "usage": {"promptTokens": 1, "completionTokens": 2, "totalTokens": 3},
            },
        )
    )
    provider = ModelProvider(
        backend="bastion",
        http_client=http,
        bastion_api_key="test-key",
    )
    with pytest.raises(BastionParseError) as exc:
        provider.complete_structured(
            model=BASTION_MODEL,
            system="s",
            user="u",
            schema=SourceExtraction,
        )
    assert exc.value.raw_text == "I cannot emit JSON."
    assert exc.value.total_tokens == 3


def test_coerce_unknown_predicates_onto_unregistered_escape() -> None:
    payload = {
        "facts": [
            {"predicate": "hearing", "proposed_predicate": None, "value": "normal"},
            {"predicate": "sleep", "value": "poor"},
            {
                "predicate": "adaptive/daily_living_skills",
                "proposed_predicate": "already_named",
                "value": "independent",
            },
        ]
    }
    out = coerce_unregistered_extraction_predicates(payload)
    assert out["facts"][0]["predicate"] == "__unregistered__"
    assert out["facts"][0]["proposed_predicate"] == "hearing"
    assert out["facts"][1]["predicate"] == "sleep"
    assert out["facts"][2]["predicate"] == "__unregistered__"
    assert out["facts"][2]["proposed_predicate"] == "already_named"


def test_bastion_unknown_predicate_parses_as_unregistered() -> None:
    extraction = {
        "facts": [
            {
                "subject": "child",
                "predicate": "vision",
                "value": "wears glasses",
                "value_text": "vision: wears glasses",
                "life_stage": "current",
                "confidence": "stated",
            }
        ]
    }
    http = _FakeHttp(
        _FakeResponse(
            200,
            {"choices": [{"finishReason": "stop", "message": {"content": json.dumps(extraction)}}]},
        )
    )
    provider = ModelProvider(
        backend="bastion",
        http_client=http,
        bastion_api_key="test-key",
    )
    result = provider.complete_structured(
        model=BASTION_MODEL,
        system="s",
        user="u",
        schema=SourceExtraction,
    )
    fact = result.data.facts[0]
    assert fact.predicate.value == "__unregistered__"
    assert fact.proposed_predicate == "vision"
