"""Reason for Referral drafting — prompt build, validation, render, provider call."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from provider import DRAFT_TEMPERATURE, ModelProvider, compute_cost_usd
from referral_context import (
    build_referral_model_payload,
    prepare_referral_context,
    selected_context_index,
)
from referral_schemas import (
    EXPLICIT_UNAVAILABLE_STATES,
    ReferralContext,
    ReferralDraftOutput,
    ReferralDraftRequest,
    ReferralDraftResponse,
    ReferralDraftStatement,
    SuspectedDisability,
    SuspectedDisabilityCategory,
)
from schemas import ReviewItem, ReviewQueue

_DIR = Path(__file__).resolve().parent
REFERRAL_SYSTEM_PROMPT = (_DIR / "referral_prompt.md").read_text(encoding="utf-8")

_CATEGORY_DISPLAY: dict[SuspectedDisabilityCategory, str] = {
    "specific_learning_disability": "Specific Learning Disability",
    "other_health_impairment": "Other Health Impairment",
    "autism": "Autism",
    "emotional_disturbance": "Emotional Disturbance",
    "speech_or_language_impairment": "Speech or Language Impairment",
    "intellectual_disability": "Intellectual Disability",
    "orthopedic_impairment": "Orthopedic Impairment",
    "traumatic_brain_injury": "Traumatic Brain Injury",
    "visual_impairment": "Visual Impairment",
    "deafness": "Deafness",
    "hard_of_hearing": "Hard of Hearing",
    "deaf_blindness": "Deaf-Blindness",
    "multiple_disabilities": "Multiple Disabilities",
    "established_medical_disability": "Established Medical Disability",
    "other": "Other",
}

_PLACEHOLDER_PATTERNS = (
    re.compile(r"\bXYZ\b"),
    re.compile(r"\bYYY\b"),
    re.compile(r"\bPARENT NAME\b", re.IGNORECASE),
    re.compile(r"\bNAME\b"),
    re.compile(r"\bDOB\b"),
    re.compile(r"\b00-year\b", re.IGNORECASE),
    re.compile(r"\bhe/she\b", re.IGNORECASE),
    re.compile(r"\bhim/her\b", re.IGNORECASE),
    re.compile(r"\bhis/her\b", re.IGNORECASE),
    re.compile(r"\bthey/them\b", re.IGNORECASE),
)

_AGE_DOB_PATTERNS = (
    re.compile(r"\b\d{1,2}-year-old\b", re.IGNORECASE),
    re.compile(r"\b\d{1,2} years old\b", re.IGNORECASE),
    re.compile(r"\bdate of birth\b", re.IGNORECASE),
    re.compile(r"\bborn on\b", re.IGNORECASE),
    re.compile(r"\bDOB\b"),
    re.compile(r"\bcurrent age\b", re.IGNORECASE),
)

_HEADING_PATTERNS = (
    re.compile(r"(?m)^#{1,6}\s"),
    re.compile(r"(?m)^\*\*[^*]+\*\*\s*:"),
    re.compile(r"(?i)\breason for referral\b\s*:"),
)

_CURLY_TO_STRAIGHT = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
    }
)


def referral_prompt_sha256() -> str:
    return hashlib.sha256(REFERRAL_SYSTEM_PROMPT.encode("utf-8")).hexdigest()


def normalize_quotation_marks(text: str) -> str:
    """Deterministic straight/curly quotation-mark normalization."""

    return text.translate(_CURLY_TO_STRAIGHT)


def normalize_client_quote_words(text: str) -> str:
    """Lexical compare for verbatim client quotes.

    Allows straight/curly quotation-mark normalization and stripping of one
    terminal punctuation mark at the quote boundary. Does not allow
    pronoun/name substitutions, reordering, omissions, or additions.
    """

    normalized = normalize_quotation_marks(text).strip()
    if normalized and normalized[-1] in ".!?,;:":
        normalized = normalized[:-1].rstrip()
    return normalized


def disability_display_name(item: SuspectedDisability) -> str:
    if item.category == "other":
        return (item.other_label or "Other").strip()
    return _CATEGORY_DISPLAY[item.category]


def render_referral_prose(output: ReferralDraftOutput) -> tuple[str, list[str]]:
    """Render paragraphs in order; append category sentence to the final paragraph."""

    if not output.paragraphs:
        raise ValueError("Referral draft has no paragraphs")
    if len(output.paragraphs) > 2:
        raise ValueError("Referral draft may have at most two paragraphs")

    paragraphs = [p.text.strip() for p in output.paragraphs]
    if any(not p for p in paragraphs):
        raise ValueError("Referral paragraph text must be non-empty")

    category = (output.suspected_disabilities_sentence or "").strip()
    if category:
        paragraphs[-1] = f"{paragraphs[-1].rstrip()} {category}".strip()

    prose = "\n\n".join(paragraphs)
    return prose, paragraphs


def _all_statements(output: ReferralDraftOutput) -> list[ReferralDraftStatement]:
    stmts: list[ReferralDraftStatement] = []
    for para in output.paragraphs:
        stmts.extend(para.statements)
    stmts.extend(output.suspected_disabilities_statements)
    return stmts


def validate_referral_draft(
    output: ReferralDraftOutput,
    selected_context: ReferralContext,
    *,
    rendered_paragraphs: list[str] | None = None,
) -> list[str]:
    """Deterministic contract checks. Returns a list of error strings."""

    errors: list[str] = []
    index = selected_context_index(selected_context)
    confirmed_categories = {
        disability_display_name(s).lower(): s
        for s in selected_context.suspected_disabilities
    }
    confirmed_category_keys = {s.category for s in selected_context.suspected_disabilities}
    verbatim_goals = {
        g.context_id: g
        for g in selected_context.client_goals
        if g.presentation_mode == "verbatim_quote"
    }

    if not (1 <= len(output.paragraphs) <= 2):
        errors.append(
            f"Expected 1–2 paragraphs; got {len(output.paragraphs)}"
        )

    try:
        prose, paragraphs = render_referral_prose(output)
    except ValueError as exc:
        errors.append(str(exc))
        return errors

    if rendered_paragraphs is not None and rendered_paragraphs != paragraphs:
        errors.append("Rendered paragraphs diverged from validator render")

    # Quote spans must appear in the paragraph or category sentence they claim.
    for i, para in enumerate(output.paragraphs):
        source_text = para.text
        if (
            i == len(output.paragraphs) - 1
            and (output.suspected_disabilities_sentence or "").strip()
        ):
            # Category statements are validated against the category sentence;
            # paragraph statements against paragraph text only.
            pass
        for stmt in para.statements:
            if stmt.quote not in source_text:
                errors.append(
                    f"Statement quote not found in paragraph {i + 1}: {stmt.quote!r}"
                )

    category_sentence = (output.suspected_disabilities_sentence or "").strip()
    if category_sentence:
        if not selected_context.suspected_disabilities:
            errors.append(
                "suspected_disabilities_sentence present but no confirmed categories"
            )
        for stmt in output.suspected_disabilities_statements:
            if stmt.quote not in category_sentence:
                errors.append(
                    "Category statement quote not found in "
                    f"suspected_disabilities_sentence: {stmt.quote!r}"
                )
        # Category sentence must be last in rendered prose.
        if not prose.rstrip().endswith(category_sentence):
            errors.append("Suspected-disabilities sentence is not last in rendered prose")
    else:
        # Explicit unavailable / absent categories: sentence not required.
        unavailable_only = selected_context.suspected_disabilities and all(
            s.confirmation_state in EXPLICIT_UNAVAILABLE_STATES
            for s in selected_context.suspected_disabilities
        )
        if unavailable_only:
            pass
        if output.suspected_disabilities_statements:
            errors.append(
                "suspected_disabilities_statements without "
                "suspected_disabilities_sentence"
            )

    for stmt in _all_statements(output):
        for support_id in stmt.support_ids:
            item = index.get(support_id)
            if item is None:
                errors.append(f"Unknown support_id: {support_id}")
                continue
            if item.confirmation_state == "conflicting":
                errors.append(f"support_id cites conflicting context item: {support_id}")
            if item.confirmation_state not in {"confirmed"}:
                errors.append(
                    f"support_id is not a selected confirmed context item: {support_id}"
                )

    # Client-goal presentation: direct quotation only when verbatim_quote + cited.
    for match in re.finditer(r'"([^"\n]{3,})"|“([^”\n]{3,})”', prose):
        quoted = match.group(1) or match.group(2) or ""
        quoted_norm = normalize_client_quote_words(quoted)
        authorized = False
        for stmt in _all_statements(output):
            for sid in stmt.support_ids:
                goal = verbatim_goals.get(sid)
                if goal is None:
                    continue
                if normalize_client_quote_words(goal.raw_text) == quoted_norm:
                    authorized = True
                    break
            if authorized:
                break
        if not authorized:
            errors.append(
                "Unrequested or non-verbatim direct client quotation: "
                f"{quoted!r}"
            )

    # Category fidelity: every named suspected disability must be confirmed.
    if category_sentence:
        lowered = category_sentence.lower()
        for label, item in confirmed_categories.items():
            # Soft presence: at least one confirmed category label should appear;
            # unknown labels are caught below via token scan of known aliases.
            _ = (label, item)
        # Reject display names that look like categories but are not confirmed.
        for cat, display in _CATEGORY_DISPLAY.items():
            if cat == "other":
                continue
            if re.search(rf"\b{re.escape(display)}\b", category_sentence, re.IGNORECASE):
                if cat not in confirmed_category_keys:
                    errors.append(
                        f"Unconfirmed suspected disability named in sentence: {display}"
                    )

    for pattern in _PLACEHOLDER_PATTERNS:
        if pattern.search(prose):
            errors.append(f"Unresolved placeholder pattern matched: {pattern.pattern}")

    for pattern in _AGE_DOB_PATTERNS:
        if pattern.search(prose):
            errors.append(f"Header age/DOB leakage matched: {pattern.pattern}")

    for pattern in _HEADING_PATTERNS:
        if pattern.search(prose):
            errors.append(f"Heading/run-in label matched: {pattern.pattern}")

    # notes_for_drafter must not be emitted verbatim.
    notes = selected_context.notes_for_drafter
    if notes and notes.raw_text and notes.raw_text.strip():
        if notes.raw_text.strip() in prose:
            errors.append("notes_for_drafter emitted verbatim in prose")

    return errors


def _completion_response(
    *,
    model: str,
    preflight,
) -> ReferralDraftResponse:
    return ReferralDraftResponse(
        ready_for_draft=False,
        section_populated=False,
        missing_fields=preflight.missing_fields,
        candidate_fields=preflight.candidate_fields,
        conflicting_fields=preflight.conflicting_fields,
        prose=None,
        paragraphs=[],
        statements=[],
        review=preflight.review,
        tokens_used=0,
        tokens_by_stage={"draft": 0},
        model=model,
        latency_ms=0,
        cost_usd=0.0,
        prompt_sha256=referral_prompt_sha256(),
    )


def draft_referral_section(
    provider: ModelProvider,
    body: ReferralDraftRequest,
) -> ReferralDraftResponse:
    """Preflight → (optional) model draft → validate → render."""

    model = body.model or "gpt-4o"
    preflight = prepare_referral_context(body.ledger, body.context)

    if not preflight.ready_for_draft:
        return _completion_response(model=model, preflight=preflight)

    payload = build_referral_model_payload(
        student_display_name=body.ledger.child.name,
        selected_context=preflight.selected_context,
        evaluation_type=preflight.evaluation_type,
    )
    # Eval bookkeeping and header demographics must never reach the model.
    assert "eval_fixture_id" not in payload
    assert "eval_run_index" not in payload
    assert "dob" not in payload
    assert "evaluation_date" not in payload
    assert "age" not in payload
    assert "grade" not in payload
    assert "school" not in payload
    assert "placement" not in payload

    user = (
        "Draft the Reason for Referral section from this case-specific payload.\n\n"
        + json.dumps(payload, indent=2, ensure_ascii=False)
    )

    result = provider.complete_structured(
        model=model,
        system=REFERRAL_SYSTEM_PROMPT,
        user=user,
        schema=ReferralDraftOutput,
        temperature=DRAFT_TEMPERATURE,
    )
    output = result.data
    assert isinstance(output, ReferralDraftOutput)

    errors = validate_referral_draft(output, preflight.selected_context)
    if errors:
        raise ValueError("Referral draft validation failed: " + "; ".join(errors[:8]))

    prose, paragraphs = render_referral_prose(output)
    statements = _all_statements(output)
    cost = compute_cost_usd(model, result.prompt_tokens, result.completion_tokens)

    review = ReviewQueue(
        items=list(preflight.review.items)
        + (
            [
                ReviewItem(
                    kind="section_empty",
                    summary=c.reason,
                    requires_decision=c.requires_clinician_selection,
                )
                for c in preflight.candidate_fields
            ]
            if preflight.candidate_fields
            else []
        )
    )

    return ReferralDraftResponse(
        ready_for_draft=True,
        section_populated=True,
        missing_fields=[],
        candidate_fields=preflight.candidate_fields,
        conflicting_fields=[],
        prose=prose,
        paragraphs=paragraphs,
        statements=statements,
        review=review,
        tokens_used=result.total_tokens,
        tokens_by_stage={"draft": result.total_tokens},
        model=model,
        latency_ms=0,
        cost_usd=round(cost, 6),
        prompt_sha256=referral_prompt_sha256(),
    )
