"""Focused Reason for Referral tests — preflight, validators, API (no pytest)."""

from __future__ import annotations

import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from fastapi.testclient import TestClient
from pydantic import ValidationError

from provider import ModelProvider, StructuredResult
from referral_context import (
    build_referral_model_payload,
    prepare_referral_context,
)
from referral_draft import (
    REFERRAL_SYSTEM_PROMPT,
    draft_referral_section,
    render_referral_prose,
    validate_referral_draft,
)
from referral_schemas import (
    AreaOfDisagreement,
    ClientGoal,
    EvaluationTypeField,
    PriorEvaluationField,
    ReferralContext,
    ReferralDraftOutput,
    ReferralDraftRequest,
    ReferralDraftStatement,
    ReferralParagraph,
    ReferralTriggerField,
    RequesterEntry,
    SuspectedDisability,
)
from schemas import Child, Fact, Ledger, Source

_DIR = Path(__file__).resolve().parent


class _RaiseProvider(ModelProvider):
    def __init__(self) -> None:
        self._client = None  # type: ignore[assignment]
        self.calls = 0

    def complete_structured(self, **kwargs: Any) -> StructuredResult:  # type: ignore[override]
        self.calls += 1
        raise AssertionError("provider must not be called during preflight tests")


class _FakeProvider(ModelProvider):
    def __init__(self, output: ReferralDraftOutput, *, fail_times: int = 0) -> None:
        self._client = None  # type: ignore[assignment]
        self._output = output
        self._fail_times = fail_times
        self.calls = 0
        self.last_user: str | None = None

    def complete_structured(self, **kwargs: Any) -> StructuredResult:  # type: ignore[override]
        self.calls += 1
        self.last_user = kwargs.get("user")
        if self.calls <= self._fail_times:
            bad = ReferralDraftOutput(
                paragraphs=[
                    ReferralParagraph(
                        text="# Reason for Referral:\nBad.",
                        statements=[
                            ReferralDraftStatement(
                                quote="Bad.",
                                statement="bad",
                                support_ids=["missing"],
                            )
                        ],
                    )
                ]
            )
            return StructuredResult(
                data=bad,
                total_tokens=10,
                prompt_tokens=5,
                completion_tokens=5,
            )
        return StructuredResult(
            data=self._output,
            total_tokens=100,
            prompt_tokens=60,
            completion_tokens=40,
        )


def _empty_ledger(*, name: str = "Jordan Lee Quinn") -> Ledger:
    return Ledger(
        child=Child(name=name, dob="2015-06-01", evaluation_date="2026-03-15"),
        ledger_version="1",
        built_at=datetime.now(timezone.utc).isoformat(),
        sources=[],
        facts=[],
    )


def _ledger_with_referral_reason(
    *,
    value: str,
    value_text: str,
    fact_id: str = "f_src_rr_001",
) -> Ledger:
    source = Source(
        id="src_rr",
        type="parent",
        date="2026-01-10",
        label="Synthetic parent form",
        content="synthetic",
    )
    fact = Fact(
        id=fact_id,
        subject="child",
        predicate="referral_reason",
        value=value,
        value_text=value_text,
        assertion="asserted",
        source_id=source.id,
        source_date=source.date,
        life_stage="school-age",
        temporality="as_of",
        confidence="stated",
    )
    return Ledger(
        child=Child(
            name="Jordan Lee Quinn",
            dob="2015-06-01",
            evaluation_date="2026-03-15",
        ),
        ledger_version="1",
        built_at=datetime.now(timezone.utc).isoformat(),
        sources=[source],
        facts=[fact],
    )


def _confirmed_private_context(**overrides: Any) -> ReferralContext:
    base: dict[str, Any] = dict(
        evaluation_type=EvaluationTypeField(
            context_id="ctx_et_1",
            normalized_value="private_psychoeducational_evaluation",
            capture_method="clinician_entered",
            confirmation_state="confirmed",
        ),
        requested_by=[
            RequesterEntry(
                context_id="ctx_req_1",
                name="Avery Quinn",
                role="parent",
                capture_method="clinician_entered",
                confirmation_state="confirmed",
            )
        ],
        referral_trigger=ReferralTriggerField(
            context_id="ctx_trig_1",
            normalized_value="clarify developmental and behavioral concerns",
            raw_text="clarify developmental and behavioral concerns",
            capture_method="clinician_entered",
            confirmation_state="confirmed",
        ),
        client_goals=[
            ClientGoal(
                context_id="ctx_goal_1",
                raw_text="We want to understand what supports will actually help.",
                normalized_value="understand helpful supports",
                capture_method="client_reported",
                confirmation_state="confirmed",
            )
        ],
        suspected_disabilities=[
            SuspectedDisability(
                context_id="ctx_sd_1",
                category="other_health_impairment",
                capture_method="clinician_confirmed",
                confirmation_state="confirmed",
            )
        ],
    )
    base.update(overrides)
    return ReferralContext(**base)


def _one_paragraph_output() -> ReferralDraftOutput:
    text = (
        "Avery Quinn, parent, requested a private psychoeducational evaluation for "
        "Jordan Lee Quinn to clarify developmental and behavioral concerns. "
        "The parents want to understand what supports will actually help."
    )
    return ReferralDraftOutput(
        paragraphs=[
            ReferralParagraph(
                text=text,
                statements=[
                    ReferralDraftStatement(
                        quote=(
                            "Avery Quinn, parent, requested a private "
                            "psychoeducational evaluation"
                        ),
                        statement="Parent requested private psychoeducational evaluation",
                        support_ids=["ctx_req_1", "ctx_et_1"],
                    ),
                    ReferralDraftStatement(
                        quote="clarify developmental and behavioral concerns",
                        statement="Referral trigger is developmental/behavioral concerns",
                        support_ids=["ctx_trig_1"],
                    ),
                    ReferralDraftStatement(
                        quote=(
                            "The parents want to understand what supports will "
                            "actually help."
                        ),
                        statement="Attributed paraphrase of parent goal",
                        support_ids=["ctx_goal_1"],
                    ),
                ],
            )
        ],
        suspected_disabilities_sentence=(
            "Suspected areas of disability include Other Health Impairment."
        ),
        suspected_disabilities_statements=[
            ReferralDraftStatement(
                quote="Other Health Impairment",
                statement="Suspected OHI",
                support_ids=["ctx_sd_1"],
            )
        ],
    )


def test_missing_evaluation_type_and_trigger_are_typed() -> None:
    provider = _RaiseProvider()
    ledger = _empty_ledger()
    context = ReferralContext()
    pre = prepare_referral_context(ledger, context)
    assert pre.ready_for_draft is False
    fields = {i.field for i in pre.missing_fields}
    assert "evaluation_type" in fields
    assert "referral_trigger" in fields
    resp = draft_referral_section(
        provider,
        ReferralDraftRequest(confirm_synthetic=True, ledger=ledger, context=context),
    )
    assert resp.tokens_used == 0
    assert provider.calls == 0


def test_iee_missing_prior_and_disagreement_skips_provider() -> None:
    provider = _RaiseProvider()
    context = ReferralContext(
        evaluation_type=EvaluationTypeField(
            context_id="ctx_et",
            normalized_value="iee",
            capture_method="clinician_entered",
            confirmation_state="confirmed",
        ),
        requested_by=[
            RequesterEntry(
                context_id="ctx_req",
                name="Morgan Benton",
                role="parent",
                capture_method="clinician_entered",
                confirmation_state="confirmed",
            )
        ],
        referral_trigger=ReferralTriggerField(
            context_id="ctx_trig",
            normalized_value="parent requested an IEE",
            capture_method="clinician_entered",
            confirmation_state="confirmed",
        ),
    )
    resp = draft_referral_section(
        provider,
        ReferralDraftRequest(
            confirm_synthetic=True,
            ledger=_empty_ledger(name="Samir Cole Benton"),
            context=context,
        ),
    )
    assert resp.ready_for_draft is False
    assert resp.tokens_used == 0
    assert provider.calls == 0
    missing = {i.field for i in resp.missing_fields}
    assert "prior_evaluation" in missing
    assert "areas_of_disagreement" in missing


def test_conflicting_load_bearing_field_skips_provider() -> None:
    provider = _RaiseProvider()
    context = _confirmed_private_context(
        referral_trigger=ReferralTriggerField(
            context_id="ctx_trig_conflict",
            normalized_value="version A",
            capture_method="document_extracted",
            confirmation_state="conflicting",
        )
    )
    resp = draft_referral_section(
        provider,
        ReferralDraftRequest(
            confirm_synthetic=True,
            ledger=_empty_ledger(),
            context=context,
        ),
    )
    assert resp.ready_for_draft is False
    assert provider.calls == 0
    assert any(i.field == "referral_trigger" for i in resp.conflicting_fields)


def test_explicit_unknown_is_not_converted_to_missing() -> None:
    context = ReferralContext(
        evaluation_type=EvaluationTypeField(
            context_id="ctx_et",
            normalized_value="private_psychoeducational_evaluation",
            capture_method="clinician_entered",
            confirmation_state="confirmed",
        ),
        requested_by=[
            RequesterEntry(
                context_id="ctx_req_unknown",
                name="unknown",
                role=None,
                capture_method="clinician_entered",
                confirmation_state="unknown",
            )
        ],
        referral_trigger=ReferralTriggerField(
            context_id="ctx_trig",
            normalized_value="concerns about learning",
            capture_method="clinician_entered",
            confirmation_state="confirmed",
        ),
    )
    pre = prepare_referral_context(_empty_ledger(), context)
    assert not any(i.field == "requested_by" for i in pre.missing_fields)
    assert pre.ready_for_draft is True


def test_ledger_referral_reason_is_candidate_not_confirmed() -> None:
    ledger = _ledger_with_referral_reason(
        value="educational progress",
        value_text="Parent is concerned about Biology.",
    )
    pre = prepare_referral_context(ledger, ReferralContext())
    assert pre.candidate_fields
    assert all(c.field == "referral_trigger" for c in pre.candidate_fields)
    assert pre.selected_context.referral_trigger is None
    assert pre.ready_for_draft is False


def test_junk_referral_reason_cannot_become_trigger() -> None:
    ledger = _ledger_with_referral_reason(
        value="attention deficit hyperactivity disorder, combined type",
        value_text="Diagnosed with ADHD Combined Type.",
        fact_id="f_misrouted",
    )
    pre = prepare_referral_context(ledger, ReferralContext())
    assert pre.selected_context.referral_trigger is None
    assert any("unconfirmed candidates only" in c.reason for c in pre.candidate_fields)


def test_raw_client_language_survives_byte_for_byte() -> None:
    raw = "We want to understand what supports will actually help."
    context = _confirmed_private_context(
        client_goals=[
            ClientGoal(
                context_id="ctx_goal_1",
                raw_text=raw,
                capture_method="client_reported",
                confirmation_state="confirmed",
            )
        ]
    )
    pre = prepare_referral_context(_empty_ledger(), context)
    assert pre.selected_context.client_goals[0].raw_text == raw
    assert pre.selected_context.client_goals[0].presentation_mode == "paraphrase"


def test_client_goal_defaults_to_paraphrase() -> None:
    goal = ClientGoal(
        context_id="ctx_goal_default",
        raw_text="Help us plan supports.",
        capture_method="client_reported",
        confirmation_state="confirmed",
    )
    assert goal.presentation_mode == "paraphrase"


def test_attributed_paraphrase_passes() -> None:
    context = _confirmed_private_context()
    pre = prepare_referral_context(_empty_ledger(), context)
    errors = validate_referral_draft(_one_paragraph_output(), pre.selected_context)
    assert errors == [], errors


def test_unrequested_direct_client_quotation_fails() -> None:
    context = _confirmed_private_context()
    pre = prepare_referral_context(_empty_ledger(), context)
    text = (
        "Avery Quinn, parent, requested a private psychoeducational evaluation for "
        "Jordan Lee Quinn to clarify developmental and behavioral concerns. "
        'The parent stated, "We want to understand what supports will actually help."'
    )
    output = ReferralDraftOutput(
        paragraphs=[
            ReferralParagraph(
                text=text,
                statements=[
                    ReferralDraftStatement(
                        quote=(
                            "Avery Quinn, parent, requested a private "
                            "psychoeducational evaluation"
                        ),
                        statement="request",
                        support_ids=["ctx_req_1", "ctx_et_1"],
                    ),
                    ReferralDraftStatement(
                        quote="clarify developmental and behavioral concerns",
                        statement="trigger",
                        support_ids=["ctx_trig_1"],
                    ),
                    ReferralDraftStatement(
                        quote="We want to understand what supports will actually help.",
                        statement="quoted goal",
                        support_ids=["ctx_goal_1"],
                    ),
                ],
            )
        ],
        suspected_disabilities_sentence=(
            "Suspected areas of disability include Other Health Impairment."
        ),
        suspected_disabilities_statements=[
            ReferralDraftStatement(
                quote="Other Health Impairment",
                statement="Suspected OHI",
                support_ids=["ctx_sd_1"],
            )
        ],
    )
    errors = validate_referral_draft(output, pre.selected_context)
    assert any("Unrequested or non-verbatim direct client quotation" in e for e in errors)


def test_verbatim_quote_allows_mark_and_terminal_punctuation_normalization() -> None:
    raw = "We want to understand what supports will actually help."
    context = _confirmed_private_context(
        client_goals=[
            ClientGoal(
                context_id="ctx_goal_1",
                raw_text=raw,
                presentation_mode="verbatim_quote",
                capture_method="client_reported",
                confirmation_state="confirmed",
            )
        ]
    )
    pre = prepare_referral_context(_empty_ledger(), context)
    # Curly quotes + missing terminal period vs raw_text period.
    text = (
        "Avery Quinn, parent, requested a private psychoeducational evaluation for "
        "Jordan Lee Quinn to clarify developmental and behavioral concerns. "
        "The parent stated, “We want to understand what supports will actually help”"
    )
    output = ReferralDraftOutput(
        paragraphs=[
            ReferralParagraph(
                text=text,
                statements=[
                    ReferralDraftStatement(
                        quote=(
                            "Avery Quinn, parent, requested a private "
                            "psychoeducational evaluation"
                        ),
                        statement="request",
                        support_ids=["ctx_req_1", "ctx_et_1"],
                    ),
                    ReferralDraftStatement(
                        quote="clarify developmental and behavioral concerns",
                        statement="trigger",
                        support_ids=["ctx_trig_1"],
                    ),
                    ReferralDraftStatement(
                        quote="We want to understand what supports will actually help",
                        statement="verbatim goal",
                        support_ids=["ctx_goal_1"],
                    ),
                ],
            )
        ],
        suspected_disabilities_sentence=(
            "Suspected areas of disability include Other Health Impairment."
        ),
        suspected_disabilities_statements=[
            ReferralDraftStatement(
                quote="Other Health Impairment",
                statement="Suspected OHI",
                support_ids=["ctx_sd_1"],
            )
        ],
    )
    errors = validate_referral_draft(output, pre.selected_context)
    assert errors == [], errors


def test_verbatim_quote_rejects_pronoun_to_name_substitution() -> None:
    context = _confirmed_private_context(
        client_goals=[
            ClientGoal(
                context_id="ctx_goal_1",
                raw_text="To get a valid assessment of his support needs.",
                presentation_mode="verbatim_quote",
                capture_method="client_reported",
                confirmation_state="confirmed",
            )
        ]
    )
    pre = prepare_referral_context(_empty_ledger(), context)
    text = (
        "Avery Quinn, parent, requested a private psychoeducational evaluation for "
        "Jordan Lee Quinn to clarify developmental and behavioral concerns. "
        'The parent stated, "To get a valid assessment of Jordan Lee Quinn\'s '
        'support needs."'
    )
    output = ReferralDraftOutput(
        paragraphs=[
            ReferralParagraph(
                text=text,
                statements=[
                    ReferralDraftStatement(
                        quote=(
                            "Avery Quinn, parent, requested a private "
                            "psychoeducational evaluation"
                        ),
                        statement="request",
                        support_ids=["ctx_req_1", "ctx_et_1"],
                    ),
                    ReferralDraftStatement(
                        quote="clarify developmental and behavioral concerns",
                        statement="trigger",
                        support_ids=["ctx_trig_1"],
                    ),
                    ReferralDraftStatement(
                        quote=(
                            "To get a valid assessment of Jordan Lee Quinn's "
                            "support needs."
                        ),
                        statement="altered quote",
                        support_ids=["ctx_goal_1"],
                    ),
                ],
            )
        ],
        suspected_disabilities_sentence=(
            "Suspected areas of disability include Other Health Impairment."
        ),
        suspected_disabilities_statements=[
            ReferralDraftStatement(
                quote="Other Health Impairment",
                statement="Suspected OHI",
                support_ids=["ctx_sd_1"],
            )
        ],
    )
    errors = validate_referral_draft(output, pre.selected_context)
    assert any("Unrequested or non-verbatim direct client quotation" in e for e in errors)


def test_model_payload_has_display_name_not_header_fields() -> None:
    context = _confirmed_private_context()
    pre = prepare_referral_context(_empty_ledger(), context)
    assert pre.ready_for_draft
    payload = build_referral_model_payload(
        student_display_name="Jordan Lee Quinn",
        selected_context=pre.selected_context,
        evaluation_type=pre.evaluation_type,
    )
    blob = json.dumps(payload)
    assert "Jordan Lee Quinn" in blob
    assert "dob" not in payload
    assert "evaluation_date" not in payload
    assert "2015-06-01" not in blob
    assert "grade" not in payload
    assert "school" not in payload
    assert "placement" not in payload
    goals = payload["selected_context"]["client_goals"]
    assert goals[0]["presentation_mode"] == "paraphrase"
    assert goals[0]["quote_ready"] is False
    assert goals[0]["client_language_use"] == "evidence_for_paraphrase_only"


def test_confirm_synthetic_false_fails_validation() -> None:
    try:
        ReferralDraftRequest.model_validate(
            {
                "confirm_synthetic": False,
                "ledger": _empty_ledger().model_dump(),
                "context": {},
            }
        )
    except ValidationError:
        return
    raise AssertionError("expected ValidationError")


def test_confirm_synthetic_missing_fails_validation() -> None:
    try:
        ReferralDraftRequest.model_validate(
            {
                "ledger": _empty_ledger().model_dump(),
                "context": {},
            }
        )
    except ValidationError:
        return
    raise AssertionError("expected ValidationError")


def test_one_paragraph_simple_render() -> None:
    context = _confirmed_private_context()
    pre = prepare_referral_context(_empty_ledger(), context)
    output = _one_paragraph_output()
    errors = validate_referral_draft(output, pre.selected_context)
    assert errors == [], errors
    prose, paragraphs = render_referral_prose(output)
    assert len(paragraphs) == 1
    assert prose.endswith("Other Health Impairment.")


def test_two_paragraph_complex_render() -> None:
    context = ReferralContext(
        evaluation_type=EvaluationTypeField(
            context_id="ctx_et_2",
            normalized_value="iee",
            capture_method="clinician_entered",
            confirmation_state="confirmed",
        ),
        requested_by=[
            RequesterEntry(
                context_id="ctx_req_2",
                name="Morgan Benton",
                role="parent",
                capture_method="clinician_entered",
                confirmation_state="confirmed",
            )
        ],
        referral_trigger=ReferralTriggerField(
            context_id="ctx_trig_2",
            normalized_value=(
                "parent requested an IEE after disagreeing with the school assessment"
            ),
            capture_method="clinician_entered",
            confirmation_state="confirmed",
        ),
        prior_evaluation=PriorEvaluationField(
            context_id="ctx_prior_2",
            organization="Lakeside Unified School District",
            report_date="2022-04-18",
            evaluation_type="psychoeducational evaluation",
            capture_method="document_extracted",
            confirmation_state="confirmed",
        ),
        areas_of_disagreement=[
            AreaOfDisagreement(
                context_id="ctx_dis_2",
                normalized_value=(
                    "parent disagrees with the school's conclusion that current "
                    "supports are sufficient"
                ),
                capture_method="clinician_entered",
                confirmation_state="confirmed",
            )
        ],
        client_goals=[
            ClientGoal(
                context_id="ctx_goal_2",
                raw_text=(
                    "I need an independent look at whether the school assessment "
                    "was accurate."
                ),
                capture_method="client_reported",
                confirmation_state="confirmed",
            )
        ],
        suspected_disabilities=[
            SuspectedDisability(
                context_id="ctx_sd_3",
                category="autism",
                capture_method="clinician_confirmed",
                confirmation_state="confirmed",
            ),
            SuspectedDisability(
                context_id="ctx_sd_4",
                category="speech_or_language_impairment",
                capture_method="clinician_confirmed",
                confirmation_state="confirmed",
            ),
        ],
    )
    pre = prepare_referral_context(_empty_ledger(name="Samir Cole Benton"), context)
    assert pre.ready_for_draft
    p1 = (
        "Morgan Benton, parent, requested an Independent Educational Evaluation "
        "for Samir Cole Benton after disagreeing with the school assessment."
    )
    p2 = (
        "A Lakeside Unified School District psychoeducational evaluation dated "
        "2022-04-18 is the prior assessment under review. The parent disagrees "
        "with the school's conclusion that current supports are sufficient and "
        "wants an independent look at whether the school assessment was accurate."
    )
    output = ReferralDraftOutput(
        paragraphs=[
            ReferralParagraph(
                text=p1,
                statements=[
                    ReferralDraftStatement(
                        quote=(
                            "Morgan Benton, parent, requested an Independent "
                            "Educational Evaluation"
                        ),
                        statement="Parent requested IEE",
                        support_ids=["ctx_req_2", "ctx_et_2"],
                    ),
                    ReferralDraftStatement(
                        quote="after disagreeing with the school assessment",
                        statement="Disagreement trigger",
                        support_ids=["ctx_trig_2"],
                    ),
                ],
            ),
            ReferralParagraph(
                text=p2,
                statements=[
                    ReferralDraftStatement(
                        quote=(
                            "Lakeside Unified School District psychoeducational "
                            "evaluation dated 2022-04-18"
                        ),
                        statement="Prior evaluation identified",
                        support_ids=["ctx_prior_2"],
                    ),
                    ReferralDraftStatement(
                        quote=(
                            "The parent disagrees with the school's conclusion that "
                            "current supports are sufficient"
                        ),
                        statement="Disagreement attributed to parent",
                        support_ids=["ctx_dis_2"],
                    ),
                    ReferralDraftStatement(
                        quote=(
                            "wants an independent look at whether the school "
                            "assessment was accurate."
                        ),
                        statement="Attributed paraphrase of parent goal",
                        support_ids=["ctx_goal_2"],
                    ),
                ],
            ),
        ],
        suspected_disabilities_sentence=(
            "Suspected areas of disability include Autism and "
            "Speech or Language Impairment."
        ),
        suspected_disabilities_statements=[
            ReferralDraftStatement(
                quote="Autism",
                statement="Suspected autism",
                support_ids=["ctx_sd_3"],
            ),
            ReferralDraftStatement(
                quote="Speech or Language Impairment",
                statement="Suspected SLI",
                support_ids=["ctx_sd_4"],
            ),
        ],
    )
    errors = validate_referral_draft(output, pre.selected_context)
    assert errors == [], errors
    prose, paragraphs = render_referral_prose(output)
    assert len(paragraphs) == 2
    assert prose.endswith("Speech or Language Impairment.")


def test_unknown_support_id_rejected() -> None:
    context = _confirmed_private_context()
    pre = prepare_referral_context(_empty_ledger(), context)
    output = _one_paragraph_output()
    output.paragraphs[0].statements[0].support_ids = ["ctx_does_not_exist"]
    errors = validate_referral_draft(output, pre.selected_context)
    assert any("Unknown support_id" in e for e in errors)


def test_quote_mismatch_rejected() -> None:
    context = _confirmed_private_context()
    pre = prepare_referral_context(_empty_ledger(), context)
    output = _one_paragraph_output()
    output.paragraphs[0].statements[0].quote = "this quote is not in the paragraph"
    errors = validate_referral_draft(output, pre.selected_context)
    assert any("quote not found" in e for e in errors)


def test_unconfirmed_category_rejected() -> None:
    context = _confirmed_private_context(suspected_disabilities=[])
    pre = prepare_referral_context(_empty_ledger(), context)
    output = _one_paragraph_output()
    errors = validate_referral_draft(output, pre.selected_context)
    assert any("no confirmed categories" in e for e in errors)


def test_three_paragraphs_rejected_by_schema() -> None:
    try:
        ReferralDraftOutput(
            paragraphs=[
                ReferralParagraph(
                    text="One.",
                    statements=[
                        ReferralDraftStatement(
                            quote="One.",
                            statement="one",
                            support_ids=["ctx_et_1"],
                        )
                    ],
                ),
                ReferralParagraph(
                    text="Two.",
                    statements=[
                        ReferralDraftStatement(
                            quote="Two.",
                            statement="two",
                            support_ids=["ctx_et_1"],
                        )
                    ],
                ),
                ReferralParagraph(
                    text="Three.",
                    statements=[
                        ReferralDraftStatement(
                            quote="Three.",
                            statement="three",
                            support_ids=["ctx_et_1"],
                        )
                    ],
                ),
            ]
        )
    except ValidationError:
        return
    raise AssertionError("expected ValidationError for 3 paragraphs")


def test_heading_run_in_rejected() -> None:
    context = _confirmed_private_context()
    pre = prepare_referral_context(_empty_ledger(), context)
    output = _one_paragraph_output()
    output.paragraphs[0].text = (
        "**Reason for Referral:** Avery Quinn, parent, requested a private "
        "psychoeducational evaluation for Jordan Lee Quinn to clarify "
        "developmental and behavioral concerns. "
        "The parents want to understand what supports will actually help."
    )
    errors = validate_referral_draft(output, pre.selected_context)
    assert any("Heading" in e for e in errors), errors


def test_placeholder_and_age_dob_leakage_rejected() -> None:
    context = _confirmed_private_context()
    pre = prepare_referral_context(_empty_ledger(), context)
    output = _one_paragraph_output()
    output.paragraphs[0].text = (
        "NAME is an 11-year-old student (DOB). Avery Quinn, parent, requested a "
        "private psychoeducational evaluation for Jordan Lee Quinn to clarify "
        "developmental and behavioral concerns. "
        "The parents want to understand what supports will actually help."
    )
    errors = validate_referral_draft(output, pre.selected_context)
    assert any("placeholder" in e.lower() or "age/dob" in e.lower() for e in errors)


def test_no_category_sentence_when_categories_unavailable() -> None:
    context = _confirmed_private_context(suspected_disabilities=[])
    pre = prepare_referral_context(_empty_ledger(), context)
    text = (
        "Avery Quinn, parent, requested a private psychoeducational evaluation for "
        "Jordan Lee Quinn to clarify developmental and behavioral concerns. "
        "The parents want to understand what supports will actually help."
    )
    output = ReferralDraftOutput(
        paragraphs=[
            ReferralParagraph(
                text=text,
                statements=[
                    ReferralDraftStatement(
                        quote=(
                            "Avery Quinn, parent, requested a private "
                            "psychoeducational evaluation"
                        ),
                        statement="request",
                        support_ids=["ctx_req_1", "ctx_et_1"],
                    ),
                    ReferralDraftStatement(
                        quote="clarify developmental and behavioral concerns",
                        statement="trigger",
                        support_ids=["ctx_trig_1"],
                    ),
                    ReferralDraftStatement(
                        quote=(
                            "The parents want to understand what supports will "
                            "actually help."
                        ),
                        statement="goal",
                        support_ids=["ctx_goal_1"],
                    ),
                ],
            )
        ],
        suspected_disabilities_sentence=None,
    )
    errors = validate_referral_draft(output, pre.selected_context)
    assert errors == [], errors


def test_fake_provider_draft_path_happy() -> None:
    provider = _FakeProvider(_one_paragraph_output())
    resp = draft_referral_section(
        provider,
        ReferralDraftRequest(
            confirm_synthetic=True,
            ledger=_empty_ledger(),
            context=_confirmed_private_context(),
            eval_fixture_id="should-not-appear",
            eval_run_index=3,
        ),
    )
    assert resp.section_populated is True
    assert resp.tokens_used > 0
    assert provider.calls == 1
    assert provider.last_user is not None
    assert "should-not-appear" not in provider.last_user
    assert "eval_run_index" not in provider.last_user
    assert "2015-06-01" not in provider.last_user
    assert "Jordan Lee Quinn" in provider.last_user
    assert resp.prose is not None
    assert "Other Health Impairment" in resp.prose


def test_api_incomplete_context_zero_spend() -> None:
    import main as main_mod

    client = TestClient(main_mod.app)
    r = client.post(
        "/draft/referral",
        json={
            "confirm_synthetic": True,
            "ledger": _empty_ledger().model_dump(),
            "context": {},
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ready_for_draft"] is False
    assert body["tokens_used"] == 0
    assert body["section_populated"] is False
    assert body["missing_fields"]


def test_api_confirm_synthetic_false_422() -> None:
    import main as main_mod

    client = TestClient(main_mod.app)
    r = client.post(
        "/draft/referral",
        json={
            "confirm_synthetic": False,
            "ledger": _empty_ledger().model_dump(),
            "context": {},
        },
    )
    assert r.status_code == 422


def test_api_valid_complete_returns_typed_draft() -> None:
    from referral_api import build_referral_router

    fake = _FakeProvider(_one_paragraph_output())
    router = build_referral_router(fake)
    endpoint = next(
        r.endpoint for r in router.routes if getattr(r, "path", None) == "/draft/referral"
    )
    req = ReferralDraftRequest(
        confirm_synthetic=True,
        ledger=_empty_ledger(),
        context=_confirmed_private_context(),
    )
    resp = endpoint(req)
    assert resp.section_populated is True
    assert resp.prose
    assert fake.calls >= 1


def test_api_validation_failure_uses_retry_budget() -> None:
    from referral_api import build_referral_router

    fake = _FakeProvider(_one_paragraph_output(), fail_times=1)
    router = build_referral_router(fake)
    endpoint = next(
        r.endpoint for r in router.routes if getattr(r, "path", None) == "/draft/referral"
    )
    req = ReferralDraftRequest(
        confirm_synthetic=True,
        ledger=_empty_ledger(),
        context=_confirmed_private_context(),
    )
    resp = endpoint(req)
    assert resp.section_populated is True
    assert fake.calls == 2


def test_existing_routes_still_registered() -> None:
    import main as main_mod

    client = TestClient(main_mod.app)
    openapi_paths = set(main_mod.app.openapi().get("paths", {}))
    assert "/draft" not in openapi_paths
    assert "/draft/history" in openapi_paths
    assert "/draft/history/plan" in openapi_paths
    assert "/draft/referral" in openapi_paths
    assert "/extract" in openapi_paths
    assert "/conflicts" in openapi_paths
    assert "/ask" in openapi_paths
    health = client.get("/health")
    assert health.status_code == 200
    referral = client.post(
        "/draft/referral",
        json={
            "confirm_synthetic": True,
            "ledger": _empty_ledger().model_dump(),
            "context": {},
        },
    )
    assert referral.status_code == 200
    assert referral.json()["tokens_used"] == 0


def test_few_shot_prompt_excludes_held_back_cases() -> None:
    lowered = REFERRAL_SYSTEM_PROMPT.lower()
    # Held-back acceptance cases must never appear in the referral prompt.
    assert "emma rose callahan" not in lowered
    assert "diego fenton" not in lowered
    assert "case 001" not in lowered
    assert "case 005" not in lowered


TESTS: list[tuple[str, Callable[[], None]]] = [
    (name, fn)
    for name, fn in globals().items()
    if name.startswith("test_") and callable(fn)
]


def main() -> int:
    print("=== Reason for Referral focused tests ===")
    results: list[tuple[str, bool]] = []
    for name, fn in TESTS:
        try:
            fn()
            print(f"  PASS  {name}")
            results.append((name, True))
        except Exception as exc:
            print(f"  FAIL  {name}: {exc}")
            traceback.print_exc()
            results.append((name, False))
    passed = sum(1 for _, ok in results if ok)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
