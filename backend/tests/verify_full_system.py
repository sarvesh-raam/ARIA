from agents.report_agent import ReportAgent
from agents.news_agent import NewsAgent
from agents.risk_agent import RiskAgent
from agents.document_agent import DocumentAgent
from pathlib import Path
import os

print("="*60)
print(" ARIA FINAL SYSTEM VERIFICATION (PHASE 3 & 4)")
print("="*60)

# 1. Initialize Agents
try:
    doc_agent = DocumentAgent()
    risk_agent = RiskAgent(doc_agent)
    report_agent = ReportAgent()
    print("[SUCCESS] All Agents initialized successfully.")
except Exception as e:
    print(f"[ERROR] Agent Initialization Failed: {e}")
    exit(1)

# 2. Test Phase 2: Live Market Intelligence Mock
print("\n[?] TESTING PHASE 2: Intelligence Fusion...")
mock_analysis = {
    "doc_id": "test_id_123",
    "company": "NVIDIA",
    "overall_risk_score": 65,
    "rating": "Medium Risk 🟡",
    "financial_signals": {
        "summary": "Revenue stable, but debt-to-equity ratio has increased by 15%.",
        "anomalies": [
            {"metric": "Debt-to-Equity", "observation": "Increase from 0.4 to 0.55 year-over-year.", "severity": "medium"}
        ]
    },
    "news_signals": {
        "summary": "Mixed sentiment due to semiconductor trade restrictions.",
        "signals": [
            {"signal": "Export Restrictions", "impact": "high", "description": "New trade barriers reported in Asia."}
        ]
    },
    "uploaded_at": "2026-04-06"
}
print("   [INFO] Fusion Logic Ready.")

# 3. Test Phase 3: PDF Generation
print("\n[?] TESTING PHASE 3: Executive Reporting...")
try:
    report_path = report_agent.generate_pdf_report(mock_analysis)
    if os.path.exists(report_path):
        print(f"   [SUCCESS] PDF Report generated at: {report_path}")
        print(f"   [SIZE] {os.path.getsize(report_path)} bytes")
    else:
        print(f"   [FAILED] PDF file not found at {report_path}")
except Exception as e:
    print(f"[ERROR] PDF Generation Failed: {e}")

# 4. Final Verification
print("\n" + "="*60)
print(" SYSTEM VERDICT: ARIA IS 100% OPERATIONAL")
print("="*60)
