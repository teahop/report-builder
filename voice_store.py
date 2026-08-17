"""Voice gate store — compiled from DECISIONS.md; review-only.

Gate strings never enter the drafting prompt (polarity firewall). The positive
channel remains the phase-1 few-shots. A1 cites the DraftBlock schema rather
than adding a judge. A4/A5 return not_applicable without a ledger.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from schemas import (
    DraftBlock,
    DraftBlockKind,
    DraftProseOutput,
    Ledger,
    ReviewItem,
)

_DIR = Path(__file__).resolve().parent
STORE_PATH = _DIR / "voice_store.json"
# report-builder/ sits at the workspace root. The ruling ledger stays outside
# this repo; the compiled store is what ships. Fall back through the old
# week-1 nesting so a nested checkout still compiles.
_DECISIONS_CANDIDATES = (
    _DIR.parent / "docs" / "project-management" / "DECISIONS.md",
    _DIR.parents[2] / "docs" / "project-management" / "DECISIONS.md",
)
DECISIONS_PATH = next(
    (path for path in _DECISIONS_CANDIDATES if path.is_file()),
    _DECISIONS_CANDIDATES[0],
)

LEDGER_LOCAL_BY_DESIGN = (
    "The ruling ledger stays local by design; the compiled store is what ships."
)

GateResult = Literal["pass", "fail", "not_applicable"]
Enforcement = Literal["deterministic", "judge"]

_LABEL_PREFIX = re.compile(r"^\*\*[^*]+\*\*:\s*")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_FINITE_VERB = re.compile(
    r"\b(is|are|was|were|has|have|had|does|did|can|could|will|would|"
    r"walked|talked|said|received|attended|reported|noted|began|started|"
    r"takes|took|met|holds)\b",
    re.IGNORECASE,
)

_THEME_WORDS: dict[str, tuple[str, ...]] = {
    "health": ("allergy", "medication", "diagnosis", "physician", "hospital", "cpap"),
    "communication": ("speech", "language", "communication", "articulation"),
    "social_emotional": ("anxiety", "attitude toward learning", "social-emotional", "behavior"),
    "life_history": ("family history", "adopted", "pregnancy", "delivery"),
}

_A7_PATTERNS = (
    re.compile(r"\breports from various sources\b", re.IGNORECASE),
    re.compile(r"\bmultiple (sources|informants|raters)\b", re.IGNORECASE),
    re.compile(r"\bsources (agree|indicate|report)\b", re.IGNORECASE),
    re.compile(r"\bacross (informants|sources|raters)\b", re.IGNORECASE),
)

# Derivation table — the store is compiled from these citations, never hand-authored.
_RECORD_SPECS: tuple[dict[str, Any], ...] = (
    {
        "id": "voice.labeled_blocks",
        "rule": "Prose is labeled blocks, not one unbroken narrative.",
        "source": "DECISIONS.md 2026-07-27",
        "source_quote": (
            "I want the reader to be able to find specific information easily "
            "by scanning the labels."
        ),
        "enforcement": "deterministic",
        "ledger_required": False,
        "cites": "schemas.DraftBlock",
        "gate": [],
        "scope": "history sections (spec §8b items 2–5)",
    },
    {
        "id": "voice.complete_sentences",
        "rule": "Complete, connected sentences inside each block; no clipped fragments.",
        "source": "DECISIONS.md 2026-07-27",
        "source_quote": "I do like prose within the blocks vs just incomplete sentences",
        "enforcement": "judge",
        "ledger_required": False,
        "gate": ["Walking at 19 months. Speech delays…"],
        "scope": "history sections (spec §8b items 2–5)",
    },
    {
        "id": "voice.one_theme_per_block",
        "rule": (
            "One theme per block; health / communication / social-emotional / "
            "life history never share a block."
        ),
        "source": "DECISIONS.md 2026-07-27",
        "source_quote": "jumpy",
        "enforcement": "judge",
        "ledger_required": False,
        "gate": [],
        "scope": "history sections (spec §8b items 2–5)",
    },
    {
        "id": "voice.supported_blocks",
        "rule": (
            "Every emitted block is supported by ledger facts; no forced or "
            "empty blocks, no \"No information was available.\""
        ),
        "source": "DECISIONS.md 2026-07-27",
        "source_quote": (
            "Use whichever the sources support, and don't force empty ones"
        ),
        "enforcement": "judge",
        "ledger_required": True,
        "gate": ["No information was available.", "No information available"],
        "scope": "history sections (spec §8b items 2–5)",
    },
    {
        "id": "voice.intervention_routing",
        "rule": (
            "Intervention routed by where it happened — school-provided to "
            "Educational History, private to the parent's account."
        ),
        "source": "DECISIONS.md 2026-07-27",
        "source_quote": (
            "Intervention history routes by WHERE the intervention happened"
        ),
        "enforcement": "judge",
        "ledger_required": True,
        "gate": [],
        "scope": "history sections (spec §8b items 2–5)",
    },
    {
        "id": "voice.write_about_child",
        "rule": "Write about the child, never the paperwork.",
        "source": "DECISIONS.md 2026-07-27 markup, failure (2)",
        "source_quote": "The IEP documents indicate…",
        "enforcement": "judge",
        "ledger_required": False,
        "gate": [
            "Records indicate…",
            "The IEP documents indicate…",
            "Reports from various sources indicate…",
            "Across various assessments…",
        ],
        "scope": "history sections (spec §8b items 2–5)",
    },
    {
        "id": "voice.informants_distinct",
        "rule": "Informants stay distinct; the reader can always tell who said what.",
        "source": "DECISIONS.md 2026-07-27 markup, failure (1)",
        "source_quote": "I like it all kept separate… It may be too homogenized.",
        "enforcement": "judge",
        "ledger_required": False,
        "gate": ["Reports from various sources indicate…"],
        "scope": "history sections (spec §8b items 2–5)",
    },
    {
        "id": "voice.no_meta_narration",
        "rule": "No meta-narration; do not close on sentences about the narrative itself.",
        "source": "DECISIONS.md 2026-07-27 markup, failure (3)",
        "source_quote": "This narrative provides a snapshot of her journey…",
        "enforcement": "judge",
        "ledger_required": False,
        "gate": [
            "This narrative provides a snapshot of her journey…",
            "emphasizing the variability observed…",
        ],
        "scope": "history sections (spec §8b items 2–5)",
    },
)


class VoiceRecord(BaseModel):
    id: str
    rule: str
    source: str
    source_quote: str
    enforcement: Enforcement
    ledger_required: bool
    gate: list[str] = Field(default_factory=list)
    cites: str | None = None
    scope: str


class VoiceGateCheck(BaseModel):
    id: str
    result: GateResult
    summary: str
    span: str | None = None
    section_key: str | None = None


class VoiceGateReport(BaseModel):
    store_sha: str
    checks: list[VoiceGateCheck] = Field(default_factory=list)

    def check_for(self, rule_id: str) -> VoiceGateCheck | None:
        for item in self.checks:
            if item.id == rule_id:
                return item
        return None


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def compiled_store_payload() -> dict[str, Any]:
    """Derive the store from DECISIONS.md citations. Never a hand-edited mapping."""

    decisions = DECISIONS_PATH.read_text(encoding="utf-8")
    records: list[dict[str, Any]] = []
    missing: list[str] = []
    for spec in _RECORD_SPECS:
        quote = spec["source_quote"]
        if quote not in decisions:
            missing.append(f"{spec['id']}: {quote!r}")
        records.append(
            {
                "id": spec["id"],
                "rule": spec["rule"],
                "source": spec["source"],
                "source_quote": spec["source_quote"],
                "enforcement": spec["enforcement"],
                "ledger_required": spec["ledger_required"],
                "gate": list(spec["gate"]),
                "cites": spec.get("cites"),
                "scope": spec["scope"],
            }
        )
    if missing:
        raise ValueError(
            "voice store citations missing from DECISIONS.md: " + "; ".join(missing)
        )
    return {
        "derived_from": "DECISIONS.md",
        "records": records,
    }


def write_voice_store(path: Path | None = None) -> Path:
    target = path or STORE_PATH
    target.write_text(_canonical_json(compiled_store_payload()), encoding="utf-8")
    return target


def load_voice_store(path: Path | None = None) -> list[VoiceRecord]:
    target = path or STORE_PATH
    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("records"), list):
        raise ValueError("voice_store.json must be an object with a records list")
    return [VoiceRecord.model_validate(row) for row in data["records"]]


def voice_store_sha(path: Path | None = None) -> str:
    target = path or STORE_PATH
    return hashlib.sha256(target.read_bytes()).hexdigest()


def decisions_ledger_status(decisions_path: Path | None = None) -> dict[str, Any]:
    """How the compiled store relates to DECISIONS.md.

    The ruling ledger lives outside the deploy. Absence is local-by-design,
    never stale or unknown — a deploy that looks broken invites shipping the ledger.
    """

    path = decisions_path if decisions_path is not None else DECISIONS_PATH
    if not path.is_file():
        return {
            "status": "local_by_design",
            "message": LEDGER_LOCAL_BY_DESIGN,
        }
    compiled = compiled_store_payload()
    on_disk = json.loads(STORE_PATH.read_text(encoding="utf-8"))
    if on_disk == compiled:
        return {
            "status": "matches_compile",
            "message": "On-disk store matches a fresh compile from the local ruling ledger.",
        }
    return {
        "status": "compile_differs",
        "message": (
            "On-disk store differs from a fresh compile of the local ruling ledger. "
            "Recompile at close-session behind propose→approve→apply."
        ),
    }


def all_gate_strings(records: list[VoiceRecord] | None = None) -> list[str]:
    rows = records if records is not None else load_voice_store()
    out: list[str] = []
    seen: set[str] = set()
    for rec in rows:
        for item in rec.gate:
            key = item.strip()
            if key and key not in seen:
                seen.add(key)
                out.append(key)
    return out


def _strip_label(text: str) -> str:
    return _LABEL_PREFIX.sub("", text.strip())


def _sentences(text: str) -> list[str]:
    body = _strip_label(text).strip()
    if not body:
        return []
    return [p.strip() for p in _SENTENCE_SPLIT.split(body) if p.strip()]


def _normalize_gate_phrase(phrase: str) -> str:
    cleaned = phrase.replace("…", "...").replace("\u2026", "...")
    cleaned = re.sub(r"\.{2,}$", "", cleaned).strip().rstrip(".").strip()
    return cleaned.lower()


def _find_gate_span(text: str, phrases: list[str], *, sentence_start: bool) -> str | None:
    if not phrases:
        return None
    sentences = _sentences(text) if sentence_start else [text]
    if not sentence_start:
        sentences = _sentences(text) or [text]
    for sentence in sentences:
        lowered = sentence.lower()
        start = _strip_label(sentence).lower() if sentence_start else lowered
        for phrase in phrases:
            needle = _normalize_gate_phrase(phrase)
            if not needle:
                continue
            if sentence_start and start.startswith(needle.lower()):
                return sentence.strip()
            if not sentence_start and needle.lower() in lowered:
                return sentence.strip()
    return None


def _prose_blocks(output: DraftProseOutput) -> list[tuple[str, str]]:
    """Return (label, prose) pairs. Falls back to rendered prose when blocks empty."""

    pairs: list[tuple[str, str]] = []
    for block in output.blocks:
        if block.kind == DraftBlockKind.TABLE:
            continue
        pairs.append((block.label, block.prose or ""))
    if pairs:
        return pairs
    if output.prose.strip():
        return [("", output.prose)]
    return []


def _check_a1(output: DraftProseOutput) -> VoiceGateCheck:
    """Cite DraftBlock: labeled typed blocks are the authored form."""

    if not output.blocks:
        if output.prose.strip():
            return VoiceGateCheck(
                id="voice.labeled_blocks",
                result="fail",
                summary=(
                    "DraftBlock schema requires labeled blocks; prose is present "
                    "with no blocks."
                ),
                span=output.prose[:180],
            )
        return VoiceGateCheck(
            id="voice.labeled_blocks",
            result="not_applicable",
            summary="No blocks and no prose to score.",
        )
    unlabeled = [b for b in output.blocks if not (b.label or "").strip()]
    if unlabeled:
        return VoiceGateCheck(
            id="voice.labeled_blocks",
            result="fail",
            summary="DraftBlock.label is empty on at least one block.",
        )
    assert DraftBlock.model_fields["label"]
    return VoiceGateCheck(
        id="voice.labeled_blocks",
        result="pass",
        summary="DraftBlock labeled blocks present (schema-enforced).",
    )


def _check_a2(output: DraftProseOutput, rec: VoiceRecord) -> VoiceGateCheck:
    planted = _find_gate_span(
        output.prose, rec.gate, sentence_start=False
    ) if rec.gate else None
    for _label, prose in _prose_blocks(output):
        sentences = _sentences(prose)
        fragment_run = 0
        for sentence in sentences:
            words = sentence.replace("…", " ").split()
            is_fragment = (
                len(words) <= 8
                and sentence.endswith((".", "…"))
                and _FINITE_VERB.search(sentence) is None
            )
            if is_fragment:
                fragment_run += 1
                if fragment_run >= 2:
                    return VoiceGateCheck(
                        id=rec.id,
                        result="fail",
                        summary="Clipped fragment style inside a labeled block.",
                        span=sentence,
                    )
            else:
                fragment_run = 0
    if planted:
        return VoiceGateCheck(
            id=rec.id,
            result="fail",
            summary="Clipped fragment style inside a labeled block.",
            span=planted,
        )
    return VoiceGateCheck(id=rec.id, result="pass", summary="Connected sentences in blocks.")


def _check_a3(output: DraftProseOutput, rec: VoiceRecord) -> VoiceGateCheck:
    for label, prose in _prose_blocks(output):
        lowered = prose.lower()
        hits = [theme for theme, words in _THEME_WORDS.items() if any(w in lowered for w in words)]
        if len(hits) >= 3:
            return VoiceGateCheck(
                id=rec.id,
                result="fail",
                summary=(
                    f"Block {label!r} mixes themes {hits} — health / communication / "
                    "social-emotional / life history must not share a block."
                ),
                span=prose[:220],
            )
    return VoiceGateCheck(id=rec.id, result="pass", summary="One theme per block.")


def _check_a4(
    output: DraftProseOutput,
    rec: VoiceRecord,
    ledger: Ledger | None,
) -> VoiceGateCheck:
    if ledger is None:
        return VoiceGateCheck(
            id=rec.id,
            result="not_applicable",
            summary="A4 is ledger-conditional; no ledger beside the draft.",
        )
    known = {f.id for f in ledger.facts}
    for block in output.blocks:
        if block.kind == DraftBlockKind.TABLE:
            continue
        prose = (block.prose or "").strip()
        span = _find_gate_span(prose, rec.gate, sentence_start=False)
        if span or not prose:
            return VoiceGateCheck(
                id=rec.id,
                result="fail",
                summary="Empty or filler block is not supported by ledger facts.",
                span=span or f"{block.label}: (empty)",
            )
        cited = {fid for stmt in block.statements for fid in stmt.fact_ids}
        if cited and not cited.intersection(known):
            return VoiceGateCheck(
                id=rec.id,
                result="fail",
                summary=f"Block {block.label!r} cites no known ledger facts.",
                span=prose[:180],
            )
    return VoiceGateCheck(id=rec.id, result="pass", summary="Emitted blocks have ledger support.")


def _check_a5(
    output: DraftProseOutput,
    rec: VoiceRecord,
    ledger: Ledger | None,
    section_key: str | None,
) -> VoiceGateCheck:
    if ledger is None:
        return VoiceGateCheck(
            id=rec.id,
            result="not_applicable",
            summary="A5 is ledger-conditional; no ledger beside the draft.",
        )
    if not section_key:
        return VoiceGateCheck(
            id=rec.id,
            result="not_applicable",
            summary="A5 needs a section_key to score intervention routing.",
        )
    parent_like = section_key in {"rater_input", "current_status_history"}
    if not parent_like:
        return VoiceGateCheck(
            id=rec.id,
            result="pass",
            summary="Section is not a parent-account destination for private intervention.",
        )
    by_id = {f.id: f for f in ledger.facts}
    sources = {s.id: s for s in ledger.sources}
    cited: list[str] = []
    for stmt in output.statements:
        cited.extend(stmt.fact_ids)
    for block in output.blocks:
        for stmt in block.statements:
            cited.extend(stmt.fact_ids)
    for fid in cited:
        fact = by_id.get(fid)
        if fact is None or fact.predicate != "intervention_tier":
            continue
        source = sources.get(fact.source_id)
        if source is not None and source.type == "school":
            return VoiceGateCheck(
                id=rec.id,
                result="fail",
                summary=(
                    "School-provided intervention appeared in a parent/rater "
                    "section; it belongs in Educational History."
                ),
                span=fact.value_text or str(fact.value),
            )
    return VoiceGateCheck(
        id=rec.id,
        result="pass",
        summary="No school-provided intervention routed into a parent/rater section.",
    )


def _check_a6(output: DraftProseOutput, rec: VoiceRecord) -> VoiceGateCheck:
    parts = [prose for _label, prose in _prose_blocks(output)]
    if output.prose:
        parts.append(output.prose)
    for text in parts:
        span = _find_gate_span(text, rec.gate, sentence_start=True)
        if span:
            return VoiceGateCheck(
                id=rec.id,
                result="fail",
                summary="Draft narrates the paperwork rather than the child.",
                span=span,
            )
    return VoiceGateCheck(id=rec.id, result="pass", summary="No banned paperwork openers.")


def _check_a7(output: DraftProseOutput, rec: VoiceRecord) -> VoiceGateCheck:
    parts = [prose for _label, prose in _prose_blocks(output)]
    if output.prose:
        parts.append(output.prose)
    for text in parts:
        span = _find_gate_span(text, rec.gate, sentence_start=False)
        if span:
            return VoiceGateCheck(
                id=rec.id,
                result="fail",
                summary="Informants are homogenized; the reader cannot tell who said what.",
                span=span,
            )
        for pattern in _A7_PATTERNS:
            match = pattern.search(text)
            if match:
                return VoiceGateCheck(
                    id=rec.id,
                    result="fail",
                    summary="Informants are homogenized; the reader cannot tell who said what.",
                    span=match.group(0),
                )
    return VoiceGateCheck(id=rec.id, result="pass", summary="Informants stay distinct.")


def _check_a8(output: DraftProseOutput, rec: VoiceRecord) -> VoiceGateCheck:
    parts = [prose for _label, prose in _prose_blocks(output)]
    if output.prose:
        parts.append(output.prose)
    for text in parts:
        span = _find_gate_span(text, rec.gate, sentence_start=False)
        if span:
            return VoiceGateCheck(
                id=rec.id,
                result="fail",
                summary="Meta-narration closer — the sentence is about the narrative, not the child.",
                span=span,
            )
    return VoiceGateCheck(id=rec.id, result="pass", summary="No meta-narration closers.")


def evaluate_voice_gates(
    output: DraftProseOutput,
    *,
    ledger: Ledger | None = None,
    section_key: str | None = None,
    store_path: Path | None = None,
) -> VoiceGateReport:
    records = load_voice_store(store_path)
    sha = voice_store_sha(store_path)
    by_id = {rec.id: rec for rec in records}
    checks: list[VoiceGateCheck] = []

    dispatch = {
        "voice.labeled_blocks": lambda rec: _check_a1(output),
        "voice.complete_sentences": lambda rec: _check_a2(output, rec),
        "voice.one_theme_per_block": lambda rec: _check_a3(output, rec),
        "voice.supported_blocks": lambda rec: _check_a4(output, rec, ledger),
        "voice.intervention_routing": lambda rec: _check_a5(
            output, rec, ledger, section_key
        ),
        "voice.write_about_child": lambda rec: _check_a6(output, rec),
        "voice.informants_distinct": lambda rec: _check_a7(output, rec),
        "voice.no_meta_narration": lambda rec: _check_a8(output, rec),
    }
    for rec in records:
        fn = dispatch.get(rec.id)
        if fn is None:
            continue
        check = fn(by_id[rec.id])
        check.section_key = section_key
        checks.append(check)
    return VoiceGateReport(store_sha=sha, checks=checks)


def review_items_from_gate(report: VoiceGateReport) -> list[ReviewItem]:
    items: list[ReviewItem] = []
    for check in report.checks:
        if check.result != "fail":
            continue
        detail = check.summary
        if check.span:
            detail = f"{check.summary} Span: {check.span}"
        items.append(
            ReviewItem(
                kind="voice_gate",
                summary=detail,
                requires_decision=True,
                voice_rule_id=check.id,
            )
        )
    return items


def merge_voice_reports(reports: list[VoiceGateReport], store_sha: str) -> VoiceGateReport:
    checks: list[VoiceGateCheck] = []
    for report in reports:
        checks.extend(report.checks)
    return VoiceGateReport(store_sha=store_sha, checks=checks)


def collect_prompt_texts() -> dict[str, str]:
    """Live generation artifacts — used by the polarity firewall test.

    Raises ImportError/OSError when the live prompts cannot be loaded so the
    firewall test can skip loudly instead of passing on an empty look.
    """

    from history_draft import HISTORY_POLICY, WRITER_PROMPT_TEMPLATE, history_system_prompt

    texts = {
        "history_policy.md": HISTORY_POLICY,
        "history_writer_prompt.md": WRITER_PROMPT_TEMPLATE,
        "history_system_prompt": history_system_prompt("Current Status & History"),
    }
    empty = [name for name, text in texts.items() if not (text or "").strip()]
    if empty:
        raise OSError(
            "live generation artifacts were empty: " + ", ".join(empty)
        )
    return texts


if __name__ == "__main__":
    path = write_voice_store()
    sha = voice_store_sha()
    print("phase=write")
    print(f"wrote {path}")
    print(f"store_sha={sha}")
