from fpdf import FPDF
from datetime import datetime
import os
from pathlib import Path

class ReportAgent:
    """
    Phase 3 Agent — The Voice (Reporter)
    Responsibilities:
      - Generate professional PDF risk reports
      - Format data into readable sections
      - Save and manage report history
    """

    def __init__(self):
        self.output_dir = Path("data/reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize(self, text: str) -> str:
        """Replace emojis and non-latin characters that standard PDF fonts can't handle."""
        if not text: return "N/A"
        # Map some common emojis to safe text equivalents
        replacements = {
            "🟢": "[LOW]", "🟡": "[MEDIUM]", "🔴": "[CRITICAL]", "•": "*",
            "©": "(c)", "®": "(r)", "™": "(TM)", "—": "--", "–": "-"
        }
        for emoji, safe_text in replacements.items():
            text = text.replace(emoji, safe_text)
            
        # FORCE REMOVE all non-Latin1 characters to prevent Helvetica range errors
        # This is a bulletproof way to ensure the PDF generator never crashes
        return text.encode('latin-1', 'ignore').decode('latin-1')

    def generate_pdf_report(self, report_data: dict) -> str:
        """
        Creates a high-end, professional ARIA Intelligence Report.
        """
        company = self._sanitize(report_data.get("company", "Unknown"))
        score = report_data.get("overall_risk_score", 0)
        rating = self._sanitize(report_data.get("rating", "Unknown"))
        doc_id = report_data.get("doc_id", "Unknown")
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_margins(15, 15, 15)
        
        # --- DARK HEADER BAR ---
        pdf.set_fill_color(22, 22, 26) # Sleek Dark Grey
        pdf.rect(0, 0, 210, 45, 'F')
        
        pdf.set_y(12)
        pdf.set_font("Helvetica", 'B', 28)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(180, 15, "ARIA INTELLIGENCE", ln=True, align='L')
        
        pdf.set_font("Helvetica", '', 12)
        pdf.set_text_color(160, 160, 160)
        pdf.cell(180, 5, "AUTONOMOUS RISK AUDIT * CONFIDENTIAL", ln=True, align='L')
        
        # --- REPORT METADATA ---
        pdf.set_y(55)
        pdf.set_text_color(80, 80, 100)
        pdf.set_font("Helvetica", 'B', 9)
        pdf.cell(90, 5, f"ENTITY: {company.upper()}")
        pdf.cell(90, 5, f"REPORT ID: {doc_id.upper()}", ln=True, align='R')
        pdf.set_font("Helvetica", '', 9)
        pdf.cell(90, 5, f"DATE: {datetime.now().strftime('%B %d, %Y')}")
        pdf.cell(90, 5, "STATUS: PHASE 4 FINAL", ln=True, align='R')
        
        pdf.ln(5)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(10)

        # --- EXECUTIVE SUMMARY BLOCK ---
        # Risk Score Indicator
        pdf.set_fill_color(248, 249, 250)
        pdf.rect(140, 75, 55, 35, 'F')
        pdf.set_xy(140, 80)
        pdf.set_font("Helvetica", 'B', 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(55, 5, "ARIA RISK SCORE", align='C', ln=True)
        
        # Score Color Logic
        if score > 70:
            pdf.set_text_color(220, 53, 69) # Red
            rating_label = "CRITICAL"
        elif score > 40:
            pdf.set_text_color(255, 165, 0) # Orange
            rating_label = "ELEVATED"
        else:
            pdf.set_text_color(40, 167, 69) # Green
            rating_label = "STABLE"
            
        pdf.set_font("Helvetica", 'B', 24)
        pdf.set_x(140)
        pdf.cell(55, 12, f"{score}/100", align='C', ln=True)
        pdf.set_font("Helvetica", 'B', 10)
        pdf.set_x(140)
        pdf.cell(55, 5, rating_label, align='C', ln=True)

        # Executive Text
        pdf.set_xy(15, 75)
        pdf.set_text_color(22, 22, 26)
        pdf.set_font("Helvetica", 'B', 16)
        pdf.cell(120, 10, "Executive Summary", ln=True)
        pdf.set_font("Helvetica", '', 11)
        summary_text = (
            f"ARIA has completed a multi-vector audit of {company}. "
            "Our engine has fused internal financial filings with real-time market news "
            "to determine a risk posture of " + rating_label + "."
        )
        pdf.multi_cell(115, 6, self._sanitize(summary_text))

        # --- SECTION 1: FINANCIALS ---
        pdf.set_y(125)
        pdf.set_fill_color(240, 242, 245)
        pdf.set_font("Helvetica", 'B', 13)
        pdf.set_text_color(22, 22, 26)
        pdf.cell(180, 10, "  1. INTERNAL FINANCIAL ANALYSIS", ln=True, fill=True)
        pdf.ln(4)
        
        fin_signals = report_data.get("financial_signals", {})
        pdf.set_font("Helvetica", 'I', 10)
        pdf.set_text_color(80, 80, 80)
        pdf.multi_cell(180, 6, self._sanitize(f"Insight: {fin_signals.get('summary', 'No internal anomalies detected.')}"))
        pdf.ln(3)
        
        anomalies = fin_signals.get("anomalies", [])
        if not anomalies:
            pdf.set_font("Helvetica", '', 10)
            pdf.set_text_color(40, 167, 69)
            pdf.cell(180, 8, "    [+] FINANCIAL OPERATIONS APPEAR STABLE", ln=True)
        else:
            for anom in anomalies:
                pdf.set_font("Helvetica", 'B', 10)
                pdf.set_text_color(22, 22, 26)
                sev = anom.get('severity', 'low').upper()
                pdf.cell(10)
                pdf.cell(170, 6, f"!! [{sev}] {anom.get('metric')}", ln=True)
                pdf.set_font("Helvetica", '', 10)
                pdf.set_text_color(100, 100, 100)
                pdf.cell(15)
                pdf.multi_cell(165, 5, self._sanitize(anom.get('observation')))
                pdf.ln(2)

        # --- SECTION 2: NEWS ---
        pdf.ln(10)
        pdf.set_fill_color(240, 242, 245)
        pdf.set_font("Helvetica", 'B', 13)
        pdf.set_text_color(22, 22, 26)
        pdf.cell(180, 10, "  2. EXTERNAL MARKET INTELLIGENCE", ln=True, fill=True)
        pdf.ln(4)
        
        news_signals = report_data.get("news_signals", {})
        pdf.set_font("Helvetica", 'I', 10)
        pdf.set_text_color(80, 80, 80)
        pdf.multi_cell(180, 6, self._sanitize(f"Sentiment: {news_signals.get('summary', 'No significant market signals found.')}"))
        pdf.ln(3)
        
        signals = news_signals.get("signals", [])
        for sig in signals:
            pdf.set_font("Helvetica", 'B', 10)
            pdf.set_text_color(22, 22, 26)
            imp = sig.get('impact', 'low').upper()
            pdf.cell(10)
            pdf.cell(170, 6, f">> [{imp}] {sig.get('signal')}", ln=True)
            pdf.set_font("Helvetica", '', 10)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(15)
            pdf.multi_cell(165, 5, self._sanitize(sig.get('description')))
            pdf.ln(2)

        # --- FOOTER ---
        pdf.set_y(-30)
        pdf.set_font("Helvetica", 'B', 8)
        pdf.set_text_color(180, 180, 180)
        pdf.cell(180, 5, "ARIA AUTONOMOUS AGENT SYSTEM", ln=True, align='C')
        pdf.set_font("Helvetica", '', 7)
        pdf.cell(180, 5, "THIS IS AN AI-GENERATED AUDIT PARA-ADVISORY ONLY. VERIFY DATA INDEPENDENTLY.", ln=True, align='C')

        # --- Save File ---
        filename = f"ARIA_Report_{company}_{doc_id}.pdf".replace(" ", "_")
        file_path = self.output_dir / filename
        pdf.output(str(file_path))
        
        return str(file_path)
