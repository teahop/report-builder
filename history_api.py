"""History package API — router for POST /draft/history."""

from __future__ import annotations

import time

from fastapi import APIRouter
from langfuse import observe

from history_compiler import compile_section_briefs
from history_draft import draft_history_package
from history_langfuse import attach_langfuse_ids
from history_schemas import (
    HistoryDraftRequest,
    HistoryDraftResponse,
    HistoryPlanRequest,
    HistoryPlanResponse,
)
from provider import DEFAULT_MODEL, ModelProvider
from retries import VALIDATION_RETRY_ATTEMPTS, run_with_validation_retries


def build_history_router(provider: ModelProvider) -> APIRouter:
    router = APIRouter()

    @router.post("/draft/history/plan")
    def plan_history(body: HistoryPlanRequest) -> HistoryPlanResponse:
        """Compile per-section case briefs from the ledger. No model call."""

        compiled = compile_section_briefs(
            body.ledger,
            conflicts=body.conflicts,
            variance=body.variance,
            structure_spec_id=body.structure_spec_id,
        )
        return HistoryPlanResponse.model_validate(compiled)

    @router.post("/draft/history")
    @observe(name="stage.draft_history")
    def draft_history(body: HistoryDraftRequest) -> HistoryDraftResponse:
        """
        Compile structure-spec plan → one model call per populated History
        section → assemble HistoryDraftPackage.

        Langfuse nests package + OpenAI generations under this span when keys
        are set.
        """

        model = body.model or DEFAULT_MODEL

        def _attempt(_attempt_i: int) -> HistoryDraftResponse:
            start = time.perf_counter()
            req = body
            if body.model is None:
                req = body.model_copy(update={"model": "gpt-4o-mini"})
            response = draft_history_package(provider, req)
            response.latency_ms = int((time.perf_counter() - start) * 1000)
            if not response.model:
                response.model = model
            return attach_langfuse_ids(response)

        return run_with_validation_retries(
            _attempt,
            max_attempts=VALIDATION_RETRY_ATTEMPTS,
            failure_prefix="History package draft failed validation after retry",
        )

    return router
