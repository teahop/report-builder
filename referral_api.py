"""Reason for Referral API — isolated router for POST /draft/referral."""

from __future__ import annotations

import time

from fastapi import APIRouter
from langfuse import get_client, observe

from provider import DEFAULT_MODEL, ModelProvider
from referral_draft import draft_referral_section
from referral_schemas import ReferralDraftRequest, ReferralDraftResponse
from retries import VALIDATION_RETRY_ATTEMPTS, run_with_validation_retries


def build_referral_router(provider: ModelProvider) -> APIRouter:
    """Attach referral drafting without altering the history /draft route."""

    router = APIRouter()

    @router.post("/draft/referral")
    @observe(name="stage.draft_referral")
    def draft_referral(body: ReferralDraftRequest) -> ReferralDraftResponse:
        """
        ReferralContext preflight → draft or typed completion response.

        Incomplete / conflicting context returns zero model tokens.
        Retries on validation failure with the shared Week 1 budget.
        """

        model = body.model or DEFAULT_MODEL

        def _attempt(_attempt_i: int) -> ReferralDraftResponse:
            start = time.perf_counter()
            response = draft_referral_section(provider, body)
            response.latency_ms = int((time.perf_counter() - start) * 1000)
            response.model = model if response.section_populated else response.model
            if not response.model:
                response.model = model
            try:
                lf = get_client()
                response.trace_id = lf.get_current_trace_id()
                response.langfuse_url = (
                    lf.get_trace_url(trace_id=response.trace_id)
                    if response.trace_id
                    else None
                )
            except Exception:
                response.trace_id = None
                response.langfuse_url = None
            return response

        return run_with_validation_retries(
            _attempt,
            max_attempts=VALIDATION_RETRY_ATTEMPTS,
            failure_prefix="Referral draft failed validation after retry",
        )

    return router
