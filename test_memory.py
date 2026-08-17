"""Read-only /memory surface — no mutating store routes, recall does not write."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from voice_store import STORE_PATH, voice_store_sha

_DIR = Path(__file__).resolve().parent
A6_DRAFT = _DIR / "evals" / "voice" / "recall" / "a6_iep_documents.json"


def test_memory_page_renders() -> None:
    import main as main_mod

    client = TestClient(main_mod.app)
    r = client.get("/memory")
    assert r.status_code == 200, r.text
    assert "text/html" in r.headers.get("content-type", "")
    body = r.text
    assert "Voice memory" in body
    assert "The store" in body
    assert "The write path" in body
    assert "Recall" in body
    assert "<th>Scope</th>" not in body


def test_memory_store_omits_scope_and_never_stale_unknown() -> None:
    import main as main_mod

    client = TestClient(main_mod.app)
    r = client.get("/memory/store")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["store_sha"] == voice_store_sha()
    assert body["path"] == "voice_store.json"
    ledger = body["ledger"]
    assert ledger["status"] in {"local_by_design", "matches_compile", "compile_differs"}
    assert ledger["status"] not in {"stale", "unknown"}
    assert "stale" not in ledger["message"].lower()
    assert "unknown" not in ledger["message"].lower()
    for rec in body["records"]:
        assert "scope" not in rec
        assert "id" in rec and "rule" in rec and "source_quote" in rec


def test_no_mutating_memory_routes_except_readonly_recall() -> None:
    import main as main_mod

    spec = main_mod.app.openapi()
    mutating = {"put", "patch", "delete"}
    posts = []
    for path, operations in spec.get("paths", {}).items():
        if not path.startswith("/memory"):
            continue
        methods = {m.lower() for m in operations}
        assert not (methods & mutating), f"{path} exposes {methods & mutating}"
        if "post" in methods:
            posts.append(path)
    assert posts == ["/memory/recall"]


def test_recall_fires_a6_and_does_not_modify_store() -> None:
    import json

    import main as main_mod

    client = TestClient(main_mod.app)
    before = STORE_PATH.read_bytes()
    draft = json.loads(A6_DRAFT.read_text(encoding="utf-8"))
    r = client.post("/memory/recall", json={"draft": draft})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["store_sha"] == voice_store_sha()
    checks = {c["id"]: c for c in body["checks"]}
    a6 = checks["voice.write_about_child"]
    assert a6["result"] == "fail"
    assert a6["span"] and "The IEP documents indicate" in a6["span"]
    a4 = checks["voice.supported_blocks"]
    a5 = checks["voice.intervention_routing"]
    assert a4["result"] == "not_applicable"
    assert a5["result"] == "not_applicable"
    assert STORE_PATH.read_bytes() == before
    items = body["review_items"]
    assert any(i["kind"] == "voice_gate" and i["voice_rule_id"] == "voice.write_about_child" for i in items)


def test_temptations_are_the_session5_slices() -> None:
    import main as main_mod

    client = TestClient(main_mod.app)
    r = client.get("/memory/temptations")
    assert r.status_code == 200, r.text
    ids = [t["id"] for t in r.json()["temptations"]]
    assert ids == ["a6", "a7", "a8"]


if __name__ == "__main__":
    tests = [
        test_memory_page_renders,
        test_memory_store_omits_scope_and_never_stale_unknown,
        test_no_mutating_memory_routes_except_readonly_recall,
        test_recall_fires_a6_and_does_not_modify_store,
        test_temptations_are_the_session5_slices,
    ]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception as exc:
            failed += 1
            print(f"FAIL {fn.__name__}: {exc}")
    raise SystemExit(1 if failed else 0)
