from typing import Dict, List
import json
from agents.document_agent import DocumentAgent
from agents.news_agent import NewsAgent
from agents.report_agent import ReportAgent
from services.groq_service import GroqService

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
        response_text = self.groq.ask(prompt)
        try:
            clean_json = response_text.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:-3].strip()
            elif clean_json.startswith("```"):
                clean_json = clean_json[3:-3].strip()
            return json.loads(clean_json)
        except:
            return {
                "financial_risk_score": 5,
                "anomalies": [],
                "summary": "Could not extract specific anomalies. Basic review suggests stable operations."
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
        rating = "Low Risk 🟢"
        if total_score > 70: rating = "Critical Risk 🔴"
        elif total_score > 40: rating = "Medium Risk 🟡"

        return {
            "doc_id": doc_id,
            "company": company_name,
            "overall_risk_score": total_score,
            "rating": rating,
            "financial_signals": financial_analysis,
            "news_signals": news_analysis,
            "timestamp": doc_info["uploaded_at"]
        }

    def generate_report(self, doc_id: str) -> str:
        """
        Run full analysis and generate a PDF report.
        Returns the path to the PDF.
        """
        analysis_data = self.run_full_analysis(doc_id)
        if "error" in analysis_data:
            raise ValueError(analysis_data["error"])
        
        pdf_path = self.report_agent.generate_pdf_report(analysis_data)
        return pdf_path
