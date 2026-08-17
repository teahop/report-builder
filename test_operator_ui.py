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
    assert "Raw file upload is later" in body
    assert "Add documents" not in body
    assert 'type="file"' not in body
    assert "./operator_live.js" in body


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
