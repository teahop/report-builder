"""Demo Day brief page — static HTML, no API key."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_brief_page_renders() -> None:
    import main as main_mod

    client = TestClient(main_mod.app)
    r = client.get("/brief")
    assert r.status_code == 200, r.text
    assert "text/html" in r.headers.get("content-type", "")
    body = r.text
    assert "Report Builder — one-page brief" in body
    assert "fact ledger" in body
    assert "voice_store.json" in body
    assert "Forget:" in body
    assert "/operator/" in body
    assert "/memory" in body
    home = client.get("/")
    assert 'href="/brief"' in home.text


if __name__ == "__main__":
    try:
        test_brief_page_renders()
        print("PASS test_brief_page_renders")
    except Exception as exc:
        print(f"FAIL test_brief_page_renders: {exc}")
        raise SystemExit(1)
    raise SystemExit(0)
