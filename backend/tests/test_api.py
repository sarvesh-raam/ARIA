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


def test_saved_analysis(client, app_module):
    assert client.get("/api/analysis/0123456789ab").status_code == 404
    assert client.get("/api/analysis/..%2F..%2Fdocuments").status_code == 404
    saved = {
        "doc_id": "0123456789ab", "company": "Acme", "overall_risk_score": 12, "rating": "Low Risk [STABLE]",
        "financial_signals": {"financial_risk_score": 5, "anomalies": [], "summary": "s"},
        "news_signals": {"news_risk_score": 0, "summary": "s", "signals": []}, "timestamp": "t",
    }
    app_module.risk_agent._analysis_path("0123456789ab").write_text(__import__("json").dumps(saved))
    r = client.get("/api/analysis/0123456789ab")
    assert r.status_code == 200 and r.json()["overall_risk_score"] == 12


def test_report_rejects_path_traversal(client):
    assert client.get("/api/report/..%2F..%2Fdocuments").status_code == 404


def test_statement_lookup_skips_table_of_contents(app_module):
    agent = app_module.risk_agent
    doc_id = "feedfacecafe"
    agent.doc_agent.chroma.add_chunks(doc_id, [
        "Index: Consolidated Statements of Operations ... page 28. Consolidated Balance Sheets ... page 29.",
        "Management discussion. Revenue grew due to strong demand.",
        "CONSOLIDATED Statements of Operations (In millions) Net sales 416,161 391,035 Net income 112,010 93,736",
        "Earnings per share 7.49 6.11 Diluted 7.46 6.08",
    ])
    found = agent._statement_chunks(doc_id, ["Statements of Operations"])
    assert found[0].startswith("CONSOLIDATED Statements of Operations")
    assert found[1].startswith("Earnings per share")  # the statement continues in the next chunk


def test_statement_lookup_with_title_in_other_case(app_module):
    # Chroma 0.4.x matches $contains case-insensitively: "Balance Sheets" must not crash on "BALANCE SHEETS"
    agent = app_module.risk_agent
    doc_id = "abcabcabcabc"
    agent.doc_agent.chroma.add_chunks(doc_id, [
        "CONSOLIDATED BALANCE SHEETS (In millions) Total assets 359,241 364,980 Total liabilities 285,508",
        "Shareholders equity 73,733 56,950",
    ])
    found = agent._statement_chunks(doc_id, ["BALANCE SHEETS", "Balance Sheets"])
    assert found[0].startswith("CONSOLIDATED BALANCE SHEETS")
    assert agent._statement_chunks(doc_id, ["Balance Sheets"]) == []  # exact-case title not present


def test_internal_errors_are_not_shown_as_document_errors(client, app_module, monkeypatch):
    app_module.doc_agent._save_metadata([{"doc_id": "0123456789ab", "company": "Acme", "uploaded_at": "x", "chunks": 1}])
    def boom(doc_id):
        raise ValueError("substring not found")  # a bug, not a problem with the user's file
    monkeypatch.setattr(app_module.risk_agent, "analyze_financial_anomalies", boom)
    r = client.get("/api/analyze/0123456789ab")
    assert r.status_code == 500 and "substring" not in r.text


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


def test_unsupported_figures_catches_invented_numbers():
    from services.validation import unsupported_figures
    source = "Net sales 143,756 124,300 Commercial paper 1,997 7,979 EPS 2.84"
    assert unsupported_figures("$143,756M vs $124,300M (+15.6%) in 2025, EPS 2.84", source) == []
    assert unsupported_figures("Total debt $13,822M", source) == ["13,822"]  # self-computed total
    assert unsupported_figures("$13.8B", source) == ["13.8"]                 # reformatted figure


def test_normalize_level():
    from services.validation import normalize_level
    assert normalize_level("HIGH") == "high"
    assert normalize_level("severe") == "low"


def test_plain_text_strips_markdown_and_citations():
    from agents.document_agent import plain_text
    raw = "Revenue was **$143,756 million**.【Document excerpt showing “Total net sales”】\n## Note\nUp 15.6%."
    assert plain_text(raw) == "Revenue was $143,756 million.\nNote\nUp 15.6%."


def test_news_search_name_strips_legal_suffixes():
    from agents.news_agent import news_search_name
    assert news_search_name("NVIDIA Corporation") == "NVIDIA"
    assert news_search_name("The Boeing Company") == "Boeing"
    assert news_search_name("Tata Sons Pvt. Ltd.") == "Tata Sons"
    assert news_search_name("Infosys") == "Infosys"


def test_cap_by_findings():
    from services.validation import cap_by_findings
    assert cap_by_findings(40, []) == 10            # no findings can't mean high risk
    assert cap_by_findings(40, ["low", "low"]) == 20
    assert cap_by_findings(40, ["low", "medium"]) == 35
    assert cap_by_findings(40, ["high"]) == 40


def test_news_top_stories_are_the_cited_articles(app_module, monkeypatch):
    news = app_module.risk_agent.news_agent
    articles = [
        {"title": f"Story {i}", "url": f"https://news.example/{i}", "source": {"name": "Wire"},
         "description": "", "publishedAt": "2026-10-01T00:00:00Z"}
        for i in range(1, 5)
    ]
    monkeypatch.setattr(news, "search_news", lambda company: articles)
    monkeypatch.setattr(news.groq, "ask_json", lambda prompt: {
        "news_risk_score": 45, "summary": "s",
        "signals": [{"signal": "Lawsuit", "impact": "medium", "description": "d", "articles": [3, 99, "x"]}],
    })
    report = news.get_risk_report("Acme")
    assert [s["title"] for s in report["top_stories"]] == ["Story 3"]  # invalid article numbers ignored
    assert report["news_risk_score"] == 35                              # capped: worst signal is medium
    assert report["window_days"] == 30


def test_overall_score_weights_financials_over_news(app_module, monkeypatch):
    agent = app_module.risk_agent
    agent.doc_agent._save_metadata([{"doc_id": "0123456789ab", "company": "Acme", "uploaded_at": "x", "chunks": 1}])
    monkeypatch.setattr(agent, "analyze_financial_anomalies", lambda doc_id: {
        "financial_risk_score": 50, "key_metrics": [], "anomalies": [], "summary": "s"})
    monkeypatch.setattr(agent.news_agent, "get_risk_report", lambda company, context: {
        "news_risk_score": 0, "summary": "s", "signals": []})
    result = agent.run_full_analysis("0123456789ab")
    assert result["overall_risk_score"] == 70
    assert result["score_breakdown"] == {"financial": 70, "financial_max": 70, "news": 0, "news_max": 30}


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
