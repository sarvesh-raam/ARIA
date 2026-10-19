from typing import Dict, Optional
from datetime import datetime
from pathlib import Path
import json
import re
from agents.document_agent import DocumentAgent
from agents.news_agent import NewsAgent
from agents.report_agent import ReportAgent
from services.groq_service import GroqService
from services.validation import clamp_score, normalize_level, require_list_of_dicts

class RiskAgent:
    """
    Phase 2 & 3 Agent — The Analyst
    Responsibilities:
      - Detect financial anomalies in documents
      - Cross-reference news signals with document data
      - Calculate the final ARIA Risk Score (0-100)
    """

    def __init__(self, doc_agent: DocumentAgent):
        self.doc_agent = doc_agent
        self.news_agent = NewsAgent()
        self.report_agent = ReportAgent()
        self.groq = GroqService()
        # Last analysis per document, so the PDF matches what the dashboard showed
        self.analyses_dir = Path("data/analyses")
        self.analyses_dir.mkdir(parents=True, exist_ok=True)

    def _analysis_path(self, doc_id: str) -> Optional[Path]:
        # doc_id comes from the URL — only accept real IDs (12 hex chars) so it can't escape the folder
        if not re.fullmatch(r"[0-9a-f]{12}", doc_id):
            return None
        return self.analyses_dir / f"{doc_id}.json"

    def load_analysis(self, doc_id: str) -> Optional[Dict]:
        path = self._analysis_path(doc_id)
        if path is None or not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def clear_analysis(self, doc_id: str):
        path = self._analysis_path(doc_id)
        if path is not None:
            path.unlink(missing_ok=True)

    def analyze_financial_anomalies(self, doc_id: str) -> Dict:
        """
        Ask the LLM to look for specific financial red flags in the document.
        """
        # We query the document for financial highlights
        query = (
            "Extract the key financial metrics for the last 2 years. "
            "Look for: Revenue, Net Income, Debt-to-Equity, and Cash Flow. "
            "Identify any unusual year-over-year drops greater than 10% or spikes in debt."
        )
        rag_data = self.doc_agent.query_document(doc_id, query)
        if rag_data["chunks_searched"] == 0:
            raise ValueError("No searchable content found for this document. Try re-uploading it.")

        prompt = f"""You are ARIA, a forensic financial auditor.
Based on the following document excerpts, identify SPECIFIC FINANCIAL ANOMALIES.

DATA FROM DOCUMENT:
{rag_data['answer']}

Output your findings in valid JSON format:
{{
  "financial_risk_score": (int 0-50),
  "anomalies": [
    {{
      "metric": "Revenue/Debt/etc",
      "observation": "description of anomaly",
      "severity": "high/medium/low"
    }}
  ],
  "summary": "1-sentence financial health summary"
}}
"""
        data = self.groq.ask_json(prompt)
        return {
            "financial_risk_score": clamp_score(data.get("financial_risk_score")),
            "anomalies": [
                {
                    "metric": str(a.get("metric", "Unspecified")),
                    "observation": str(a.get("observation", "")),
                    "severity": normalize_level(a.get("severity")),
                }
                for a in require_list_of_dicts(data, "anomalies")
            ],
            "summary": str(data.get("summary", "")),
        }

    def run_full_analysis(self, doc_id: str, progress_callback=None) -> Dict:
        """
        The main pipeline for Phase 2:
        1. Get document metadata (company name)
        2. Analyze financial anomalies via RAG
        3. Fetch and analyze live news
        4. Fuse data and calculate final score
        """
        if progress_callback: progress_callback(10, "Starting multi-source analysis...")
        # Get company name from metadata
        docs = self.doc_agent.list_documents()
        doc_info = next((d for d in docs if d["doc_id"] == doc_id), None)
        
        if not doc_info:
            return {"error": "Document not found"}

        company_name = doc_info.get("company", "Unknown Company")

        # 1. Financial Analysis
        if progress_callback: progress_callback(25, f"Analyzing financial health for {company_name}...")
        financial_analysis = self.analyze_financial_anomalies(doc_id)

        # 2. News Analysis
        if progress_callback: progress_callback(60, f"Searching live news for {company_name}...")
        news_analysis = self.news_agent.get_risk_report(company_name)

        # 3. Final Fusion & Scoring
        if progress_callback: progress_callback(85, "Fusing signals and calculating ARIA score...")
        # Calculation: Financial Score (0-50) + News Score (0-50)
        f_score = financial_analysis.get("financial_risk_score", 0)
        n_score = news_analysis.get("news_risk_score", 0)
        total_score = f_score + n_score

        # Determine overall rating
        rating = "Low Risk [STABLE]"
        if total_score > 70: rating = "Critical Risk [CRITICAL]"
        elif total_score > 40: rating = "Medium Risk [ELEVATED]"

        result = {
            "doc_id": doc_id,
            "company": company_name,
            "overall_risk_score": total_score,
            "rating": rating,
            "financial_signals": financial_analysis,
            "news_signals": news_analysis,
            "timestamp": datetime.now().isoformat(),
        }
        path = self._analysis_path(doc_id)
        if path is not None:
            path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result

    def generate_report(self, doc_id: str) -> str:
        """
        Generate a PDF report from the latest analysis (running one if none exists).
        Returns the path to the PDF.
        """
        analysis_data = self.load_analysis(doc_id) or self.run_full_analysis(doc_id)
        if "error" in analysis_data:
            raise ValueError(analysis_data["error"])
        
        pdf_path = self.report_agent.generate_pdf_report(analysis_data)
        return pdf_path
