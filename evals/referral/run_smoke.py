"""One synthetic Reason for Referral smoke — hard stop after a single draft."""

from __future__ import annotations

import json
import sys
import time
import re
from datetime import datetime, timezone
from pathlib import Path

_WEEK1 = Path(__file__).resolve().parents[2]
if str(_WEEK1) not in sys.path:
    sys.path.insert(0, str(_WEEK1))

from dotenv import load_dotenv

load_dotenv(_WEEK1 / ".env")

from provider import DEFAULT_MODEL, DRAFT_TEMPERATURE, ModelProvider
from referral_context import prepare_referral_context
from referral_draft import (
    draft_referral_section,
    referral_prompt_sha256,
)
from referral_schemas import (
    ClientGoal,
    EvaluationTypeField,
    PresentingConcern,
    ReferralContext,
    ReferralDraftRequest,
    ReferralTriggerField,
    RequesterEntry,
    SuspectedDisability,
)
from retries import VALIDATION_RETRY_ATTEMPTS, run_with_validation_retries
from schemas import Child, Ledger

_DIR = Path(__file__).resolve().parent
_TRACES = _DIR / "traces"


def _synthetic_complete_context() -> tuple[Ledger, ReferralContext]:
    ledger = Ledger(
        child=Child(
            name="Casey Morgan Ellison",
            dob="2014-09-12",
            evaluation_date="2026-02-20",
        ),
        ledger_version="1",
        built_at=datetime.now(timezone.utc).isoformat(),
        sources=[],
        facts=[],
    )
    context = ReferralContext(
        evaluation_type=EvaluationTypeField(
            context_id="ctx_smoke_et",
            normalized_value="private_psychoeducational_evaluation",
            capture_method="clinician_entered",
            confirmation_state="confirmed",
        ),
        requested_by=[
            RequesterEntry(
                context_id="ctx_smoke_req",
                name="Riley Ellison",
                role="parent",
                capture_method="clinician_entered",
                confirmation_state="confirmed",
            )
        ],
        referral_trigger=ReferralTriggerField(
            context_id="ctx_smoke_trig",
            normalized_value=(
                "clarify learning and attention concerns that persist despite "
                "classroom supports"
            ),
            capture_method="clinician_entered",
            confirmation_state="confirmed",
        ),
        presenting_concerns=[
            PresentingConcern(
                context_id="ctx_smoke_pc1",
                normalized_value="slow work completion and lost assignments",
                capture_method="client_reported",
                confirmation_state="confirmed",
            )
        ],
        client_goals=[
            ClientGoal(
                context_id="ctx_smoke_goal",
                raw_text="I want clear recommendations for how to help at home and school.",
                normalized_value="obtain clear home and school recommendations",
                presentation_mode="paraphrase",
                capture_method="client_reported",
                confirmation_state="confirmed",
            )
        ],
        suspected_disabilities=[
            SuspectedDisability(
                context_id="ctx_smoke_sd1",
                category="specific_learning_disability",
                capture_method="clinician_confirmed",
                confirmation_state="confirmed",
            ),
            SuspectedDisability(
                context_id="ctx_smoke_sd2",
                category="other_health_impairment",
                capture_method="clinician_confirmed",
                confirmation_state="confirmed",
            ),
        ],
    )
    return ledger, context


def main() -> None:
    _TRACES.mkdir(parents=True, exist_ok=True)
    ledger, context = _synthetic_complete_context()
    pre = prepare_referral_context(ledger, context)
    assert pre.ready_for_draft, (pre.missing_fields, pre.conflicting_fields)

    provider = ModelProvider()
    body = ReferralDraftRequest(
        confirm_synthetic=True,
        ledger=ledger,
        context=context,
        model=DEFAULT_MODEL,
        eval_fixture_id="synthetic_referral_smoke",
        eval_run_index=0,
    )

    start = time.perf_counter()
    try:
        response = run_with_validation_retries(
            lambda _attempt: draft_referral_section(provider, body),
            max_attempts=VALIDATION_RETRY_ATTEMPTS,
            failure_prefix="Referral smoke failed validation after retry",
        )
    except Exception as exc:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        trace_path = _TRACES / f"smoke-{stamp}.jsonl"
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "fixture_id": "synthetic_referral_smoke",
            "model": DEFAULT_MODEL,
            "temperature": DRAFT_TEMPERATURE,
            "prompt_sha256": referral_prompt_sha256(),
            "status": "validation_failed",
            "error": str(exc),
            "observed_failure": str(exc),
            "latency_ms": int((time.perf_counter() - start) * 1000),
        }
        trace_path.write_text(
            json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print("=== Reason for Referral — one synthetic smoke (FAILED validation) ===")
        print(f"trace: {trace_path}")
        print(f"error: {exc}")
        print("STOP: hand failure to TJ. Do not sweep. Do not revise prompt without a ruling.")
        raise SystemExit(1) from exc

    latency_ms = int((time.perf_counter() - start) * 1000)
    response.latency_ms = latency_ms

    # Re-validate from rendered path for the handback checklist.
    support_ok = True
    category_last_ok = bool(response.prose) and (
        "Specific Learning Disability" in (response.prose or "")
        or "Other Health Impairment" in (response.prose or "")
    )
    if response.paragraphs:
        category_last_ok = category_last_ok and (
            "Specific Learning Disability" in response.paragraphs[-1]
            or "Other Health Impairment" in response.paragraphs[-1]
        )
    prose = response.prose or ""
    direct_client_quote_present = bool(
        re.search(r'"[^"\n]{3,}"|“[^”\n]{3,}”', prose)
    )
    leakage_ok = True
    for bad in ("2014-09-12", "DOB", "year-old"):
        if bad.lower() in prose.lower():
            leakage_ok = False

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    trace_path = _TRACES / f"smoke-{stamp}.jsonl"
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "fixture_id": "synthetic_referral_smoke",
        "model": response.model,
        "temperature": DRAFT_TEMPERATURE,
        "prompt_sha256": response.prompt_sha256 or referral_prompt_sha256(),
        "tokens_used": response.tokens_used,
        "latency_ms": response.latency_ms,
        "cost_usd": response.cost_usd,
        "paragraph_count": len(response.paragraphs),
        "prose": response.prose,
        "paragraphs": response.paragraphs,
        "statements": [s.model_dump() for s in response.statements],
        "checks": {
            "support_id_validation": support_ok and response.section_populated,
            "category_last": category_last_ok,
            "client_goal_presentation_mode": "paraphrase",
            "direct_client_quote_present": direct_client_quote_present,
            "client_quote_fidelity": "not_applicable",
            "header_placeholder_leakage_clear": leakage_ok,
        },
        "ready_for_draft": response.ready_for_draft,
        "section_populated": response.section_populated,
    }
    trace_path.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")

    print("=== Reason for Referral — one synthetic smoke ===")
    print(f"trace: {trace_path}")
    print(f"model: {response.model}")
    print(f"temperature: {DRAFT_TEMPERATURE}")
    print(f"prompt_sha256: {record['prompt_sha256']}")
    print(f"tokens: {response.tokens_used}")
    print(f"latency_ms: {response.latency_ms}")
    print(f"cost_usd: {response.cost_usd}")
    print(f"paragraph_count: {len(response.paragraphs)}")
    print(f"checks: {json.dumps(record['checks'], indent=2)}")
    print("--- prose ---")
    print(response.prose)
    print("--- end ---")
    print("STOP: hand prose to TJ. Do not sweep. Do not revise prompt without a ruling.")


if __name__ == "__main__":
    main()
