"""Phase 1 operator canvas — served from static/operator; no file-upload route."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

_DIR = Path(__file__).resolve().parent
_CACHE = _DIR / "evals" / "cache" / "fixture_001_ledger.json"


def test_operator_page_renders() -> None:
    import main as main_mod

    client = TestClient(main_mod.app)
    r = client.get("/operator/", follow_redirects=True)
    assert r.status_code == 200, r.text
    assert "text/html" in r.headers.get("content-type", "")
    body = r.text
    assert "operator · phase 1" in body
    assert "Load fixture packet" in body
    assert "Load cached ledger" in body
    assert "Extract ledger" in body
    assert "Save as cached ledger" in body
    assert "Raw file upload is later" in body
    assert "Add documents" not in body
    assert 'type="file"' not in body
    assert "./operator_live.js" in body
    assert "Skip entailment" in body


def test_operator_redirects_to_trailing_slash() -> None:
    import main as main_mod

    client = TestClient(main_mod.app, follow_redirects=False)
    r = client.get("/operator")
    assert r.status_code in {307, 308}
    loc = r.headers.get("location", "")
    assert loc.endswith("/operator/") or loc.rstrip("/").endswith("/operator")


def test_operator_assets_served() -> None:
    import main as main_mod

    client = TestClient(main_mod.app)
    js = client.get("/operator/operator_live.js")
    assert js.status_code == 200, js.text
    assert "OperatorLive" in js.text
    assert "skip_entailment" in js.text
    assert "saveCached001" in js.text
    assert "Draft is on the page; open Verify." in js.text
    assert "failed validation after 3 retry attempts" not in js.text
    support = client.get("/operator/support.js")
    assert support.status_code == 200, support.text


def test_cached_ledger_001_is_read_only() -> None:
    import main as main_mod

    before = _CACHE.read_bytes()
    client = TestClient(main_mod.app)
    r = client.get("/fixtures/cached_ledger_001")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["child"]["name"] == "Emma Rose Callahan"
    assert body["facts"]
    assert body["sources"]
    after = _CACHE.read_bytes()
    assert after == before


def test_save_cached_ledger_001_writes_wrapper_not_production_file() -> None:
    import json
    import tempfile
    from pathlib import Path

    import main as main_mod

    original_cache = main_mod._CACHE_LEDGER_001
    production_bytes = original_cache.read_bytes()
    ledger = json.loads(production_bytes.decode("utf-8"))["ledger"]
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "fixture_001_ledger.json"
        main_mod._CACHE_LEDGER_001 = dest
        try:
            client = TestClient(main_mod.app)
            r = client.post(
                "/fixtures/cached_ledger_001",
                json={
                    "confirm_synthetic": True,
                    "model": "gpt-4o-mini",
                    "ledger": ledger,
                },
            )
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["child_name"] == "Emma Rose Callahan"
            assert body["fact_count"] == len(ledger["facts"])
            saved = json.loads(dest.read_text(encoding="utf-8"))
            assert saved["source"] == "operator_save"
            assert "ledger" in saved
            got = client.get("/fixtures/cached_ledger_001")
            assert got.status_code == 200
            assert got.json()["child"]["name"] == "Emma Rose Callahan"
        finally:
            main_mod._CACHE_LEDGER_001 = original_cache
    assert original_cache.read_bytes() == production_bytes


def test_save_cached_ledger_001_rejects_other_child() -> None:
    import json
    import tempfile
    from pathlib import Path

    import main as main_mod

    original_cache = main_mod._CACHE_LEDGER_001
    ledger = json.loads(original_cache.read_text(encoding="utf-8"))["ledger"]
    ledger["child"]["name"] = "Diego Fenton"
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "fixture_001_ledger.json"
        main_mod._CACHE_LEDGER_001 = dest
        try:
            client = TestClient(main_mod.app)
            r = client.post(
                "/fixtures/cached_ledger_001",
                json={"confirm_synthetic": True, "ledger": ledger},
            )
            assert r.status_code == 400, r.text
            assert not dest.exists()
        finally:
            main_mod._CACHE_LEDGER_001 = original_cache


def test_no_operator_upload_endpoint() -> None:
    import main as main_mod

    spec = main_mod.app.openapi()
    for path, operations in spec.get("paths", {}).items():
        methods = {m.lower() for m in operations}
        if path.startswith("/operator"):
            assert "post" not in methods
            assert "put" not in methods
            assert "patch" not in methods
    assert "/ingest" in spec.get("paths", {})


if __name__ == "__main__":
    tests = [
        test_operator_page_renders,
        test_operator_redirects_to_trailing_slash,
        test_operator_assets_served,
        test_cached_ledger_001_is_read_only,
        test_save_cached_ledger_001_writes_wrapper_not_production_file,
        test_save_cached_ledger_001_rejects_other_child,
        test_no_operator_upload_endpoint,
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
