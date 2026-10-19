"""
ARIA backend smoke tests — run without real API keys or network LLM calls.

Usage (from backend/):
    pytest tests/test_api.py
"""
import importlib
import os
import sys
from pathlib import Path

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture(scope="module")
def app_module(tmp_path_factory):
    # main.py stores data relative to the working directory — keep it out of the repo
    os.chdir(tmp_path_factory.mktemp("aria"))
    os.environ.setdefault("GROQ_API_KEY", "test-key-not-used")
    os.environ["ADMIN_API_KEY"] = ""
    os.environ["RATE_LIMIT_PER_MINUTE"] = "0"
    import services.security
    importlib.reload(services.security)
    import main
    return importlib.reload(main)


@pytest.fixture(scope="module")
def client(app_module):
    return TestClient(app_module.app, raise_server_exceptions=False)


def upload(client, name, data):
    return client.post("/api/upload", files={"file": (name, data, "application/pdf")})


# ── API ─────────────────────────────────────────────────────────

def test_health(client):
    assert client.get("/").status_code == 200


def test_upload_rejects_non_pdf(client):
    assert upload(client, "notes.txt", b"hello").status_code == 400


def test_upload_rejects_empty_file(client):
    assert upload(client, "empty.pdf", b"").status_code == 400


def test_upload_rejects_corrupt_pdf(client):
    r = upload(client, "bad.pdf", b"garbage")
    assert r.status_code == 400
    assert "could not be read" in r.json()["detail"]


def test_upload_rejects_oversized_file(client, app_module, monkeypatch):
    monkeypatch.setattr(app_module, "MAX_UPLOAD_MB", 0)
    assert upload(client, "big.pdf", b"%PDF-1.4 data").status_code == 413


def test_delete_disabled_without_admin_key(client):
    assert client.delete("/api/documents/abcdef123456").status_code == 403


def test_document_list_hides_sensitive_fields(client, app_module):
    app_module.doc_agent._save_metadata([{
        "doc_id": "abcdef123456", "filename": "secret.pdf", "company": "Acme",
        "uploaded_at": "2026-01-01T00:00:00", "chunks": 3, "preview": "confidential text",
    }])
    docs = client.get("/api/documents").json()
    assert docs == [{"doc_id": "abcdef123456", "company": "Acme", "uploaded_at": "2026-01-01T00:00:00", "chunks": 3}]


def test_analyze_unknown_document_is_404(client):
    assert client.get("/api/analyze/000000000000").status_code == 404


def test_report_rejects_path_traversal(client):
    assert client.get("/api/report/..%2F..%2Fdocuments").status_code == 404


# ── Security helpers ────────────────────────────────────────────

def test_rate_limiter_blocks_after_limit():
    from services.security import RateLimiter
    limited = FastAPI()

    @limited.get("/", dependencies=[Depends(RateLimiter(2))])
    def ping():
        return {}

    c = TestClient(limited)
    codes = [c.get("/", headers={"X-Forwarded-For": f"1.2.3.{i}, 10.0.0.5"}).status_code for i in range(3)]
    assert codes == [200, 200, 429]  # spoofed left-most entries don't reset the limit


# ── LLM output validation ───────────────────────────────────────

def test_clamp_score():
    from services.groq_service import LLMError
    from services.validation import clamp_score
    assert clamp_score("30") == 30
    assert clamp_score(80) == 50
    assert clamp_score(-5) == 0
    with pytest.raises(LLMError):
        clamp_score("high")


def test_normalize_level():
    from services.validation import normalize_level
    assert normalize_level("HIGH") == "high"
    assert normalize_level("severe") == "low"


def test_news_search_name_strips_legal_suffixes():
    from agents.news_agent import news_search_name
    assert news_search_name("NVIDIA Corporation") == "NVIDIA"
    assert news_search_name("The Boeing Company") == "Boeing"
    assert news_search_name("Tata Sons Pvt. Ltd.") == "Tata Sons"
    assert news_search_name("Infosys") == "Infosys"


# ── PDF report ──────────────────────────────────────────────────

def test_pdf_text_replaces_unsupported_characters():
    from agents.report_agent import to_pdf_text
    assert to_pdf_text("₹3,000 — 60 % year‑over‑year") == "Rs.3,000 -- 60 % year-over-year"


def test_report_handles_unicode_and_unsafe_company_names(app_module):
    from agents.report_agent import ReportAgent
    data = {
        "doc_id": "abcdef123456", "overall_risk_score": 72, "rating": "Critical",
        "financial_signals": {"summary": "s", "anomalies": [{"metric": "Revenue (₹ crore)", "observation": "fell"}]},
        "news_signals": {"summary": "中国 🚀", "signals": [{"signal": "₹ risk", "impact": "high", "description": "d"}]},
    }
    for company in ["AT&T / Inc", "Société Générale", "   "]:
        path = Path(ReportAgent().generate_pdf_report({**data, "company": company}))
        assert path.exists() and path.parent.name == "reports"
