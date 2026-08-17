"""Read-only /memory surface for Session 5 — store display + recall. No writes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from schemas import DraftProseOutput
from voice_store import (
    STORE_PATH,
    VoiceRecord,
    decisions_ledger_status,
    evaluate_voice_gates,
    load_voice_store,
    review_items_from_gate,
    voice_store_sha,
)

_DIR = Path(__file__).resolve().parent
_PAGE = _DIR / "static" / "memory.html"
RECALL_DIR = _DIR / "evals" / "voice" / "recall"

TEMPTATIONS: tuple[dict[str, str], ...] = (
    {
        "id": "a6",
        "rule_id": "voice.write_about_child",
        "title": "Paperwork opener",
        "file": "a6_iep_documents.json",
        "what_it_tempts": "A draft that narrates the IEP instead of the child.",
    },
    {
        "id": "a7",
        "rule_id": "voice.informants_distinct",
        "title": "Blended informants",
        "file": "a7_blended_informants.json",
        "what_it_tempts": "A draft that homogenizes who said what.",
    },
    {
        "id": "a8",
        "rule_id": "voice.no_meta_narration",
        "title": "Meta-narration closer",
        "file": "a8_meta_narration.json",
        "what_it_tempts": "A draft that closes on the narrative itself.",
    },
)


class MemoryRecallRequest(BaseModel):
    draft: DraftProseOutput
    section_key: str | None = Field(default=None)


def _public_record(rec: VoiceRecord) -> dict:
    data = rec.model_dump()
    data.pop("scope", None)
    return data


def _load_temptation(filename: str) -> dict:
    path = (RECALL_DIR / filename).resolve()
    if not path.is_file() or not path.is_relative_to(RECALL_DIR.resolve()):
        raise HTTPException(status_code=404, detail=f"Temptation not found: {filename}")
    return DraftProseOutput.model_validate_json(path.read_text(encoding="utf-8")).model_dump()


def build_memory_router() -> APIRouter:
    router = APIRouter()

    @router.get("/memory")
    def memory_page() -> FileResponse:
        if not _PAGE.is_file():
            raise HTTPException(status_code=404, detail="memory page missing")
        return FileResponse(_PAGE, media_type="text/html; charset=utf-8")

    @router.get("/memory/store")
    def memory_store() -> dict:
        records = load_voice_store()
        ledger = decisions_ledger_status()
        return {
            "store_sha": voice_store_sha(),
            "derived_from": "DECISIONS.md",
            "path": "voice_store.json",
            "ledger": ledger,
            "records": [_public_record(rec) for rec in records],
        }

    @router.get("/memory/temptations")
    def memory_temptations() -> dict:
        items = []
        for row in TEMPTATIONS:
            items.append(
                {
                    "id": row["id"],
                    "rule_id": row["rule_id"],
                    "title": row["title"],
                    "what_it_tempts": row["what_it_tempts"],
                    "draft": _load_temptation(row["file"]),
                }
            )
        return {"temptations": items, "store_sha": voice_store_sha()}

    @router.post("/memory/recall")
    def memory_recall(body: MemoryRecallRequest) -> dict:
        """Score a draft against the compiled store. Does not write voice_store.json."""

        before = STORE_PATH.read_bytes()
        report = evaluate_voice_gates(body.draft, section_key=body.section_key)
        after = STORE_PATH.read_bytes()
        if after != before:
            raise HTTPException(
                status_code=500,
                detail="recall mutated voice_store.json — that is a bug",
            )
        return {
            "store_sha": report.store_sha,
            "checks": [c.model_dump() for c in report.checks],
            "review_items": [i.model_dump() for i in review_items_from_gate(report)],
        }

    return router
