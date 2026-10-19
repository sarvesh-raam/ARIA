from fpdf import FPDF
from fpdf.enums import XPos, YPos
from fpdf.fonts import FontFace
from datetime import datetime, timezone
from pathlib import Path
import re
import unicodedata

# Characters the built-in PDF fonts (latin-1) can't draw, mapped to readable equivalents
PDF_REPLACEMENTS = {
    "🟢": "[LOW]", "🟡": "[MEDIUM]", "🔴": "[CRITICAL]", "•": "*",
    "™": "(TM)", "—": "--", "–": "-", "‑": "-", "‐": "-",
    "₹": "Rs.", "€": "EUR", "‘": "'", "’": "'", "“": '"', "”": '"', "…": "...",
    " ": " ", " ": " ", "​": "", "【": "[", "】": "]",
    # Math and arrows the LLM uses in figures ("−5.7%", "≈15%", "₹53,001 cr → ₹60,914 cr")
    "−": "-", "≈": "~", "→": "->", "←": "<-", "≥": ">=", "≤": "<=", "×": "x", "∆": "change", "Δ": "change",
}


def to_pdf_text(text: str) -> str:
    """Make text safe for the built-in latin-1 PDF fonts without losing meaning."""
    for char, safe_text in PDF_REPLACEMENTS.items():
        text = text.replace(char, safe_text)
    # Decompose remaining characters (e.g. ligatures) and replace anything still unsupported
    text = unicodedata.normalize("NFKC", text)
    return text.encode("latin-1", "replace").decode("latin-1")


class SafeFPDF(FPDF):
    """FPDF that sanitizes every piece of text, so a stray character can't crash the report."""

    def normalize_text(self, text):
        return super().normalize_text(to_pdf_text(text))


# Same palette as the dashboard (frontend/src/app/globals.css, light theme)
INK = (16, 24, 40)
MUTED = (102, 112, 133)
LINE = (228, 231, 236)
SUBTLE = (242, 244, 247)
ACCENT = (29, 78, 216)
TONE_COLORS = {"stable": (3, 152, 85), "elevated": (220, 104, 3), "critical": (217, 45, 32)}
LEVEL_COLORS = {"high": TONE_COLORS["critical"], "medium": TONE_COLORS["elevated"], "low": MUTED}

MARGIN = 18
DISCLAIMER = "AI-generated analysis for information only. Verify figures against the source document before relying on them."


def score_tone(score: int) -> str:
    # Same bands as risk_agent.py: >70 critical, >40 elevated
    return "critical" if score > 70 else "elevated" if score > 40 else "stable"


def rating_label(rating: str) -> str:
    """"Medium Risk [ELEVATED]" -> "Medium risk"."""
    label = re.sub(r"\s*\[.*\]\s*", "", rating or "").strip()
    return label[:1].upper() + label[1:].lower() if label else "Unrated"


def format_timestamp(iso: str) -> str:
    """ISO timestamp -> "20 Oct 2026, 19:06 UTC". Older records have no offset and are UTC."""
    try:
        moment = datetime.fromisoformat(iso)
    except (TypeError, ValueError):
        try:
            # Python 3.9 only parses 3- or 6-digit fractions; fall back to whole seconds
            moment = datetime.fromisoformat(str(iso)[:19])
        except ValueError:
            return ""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).strftime("%d %b %Y, %H:%M UTC")


def format_date(iso: str) -> str:
    try:
        return datetime.fromisoformat((iso or "").replace("Z", "+00:00")).strftime("%d %b %Y")
    except ValueError:
        return ""


class ReportPDF(SafeFPDF):
    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*MUTED)
        self.cell(self.epw - 25, 5, DISCLAIMER)
        self.cell(25, 5, f"Page {self.page_no()} of {{nb}}", align="R")


class ReportAgent:
    """
    Phase 3 Agent — The Voice (Reporter)
    Responsibilities:
      - Generate PDF risk reports that match the dashboard
      - Format data into readable sections
    """

    def __init__(self):
        self.output_dir = Path("data/reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ── Layout helpers ───────────────────────────────────────────

    @staticmethod
    def _text(pdf: FPDF, text: str, size: float = 10, style: str = "", color=INK, height: float = 5.2):
        """A full-width paragraph that wraps and moves the cursor below it."""
        pdf.set_font("Helvetica", style, size)
        pdf.set_text_color(*color)
        pdf.multi_cell(0, height, text or "", align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    @staticmethod
    def _section_title(pdf: FPDF, title: str, aside: str = ""):
        pdf.ln(3)
        # Keep a title together with at least a few lines of its content
        if pdf.get_y() > pdf.h - 50:
            pdf.add_page()
        y = pdf.get_y()
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*INK)
        pdf.cell(pdf.epw - 40, 7, title)
        if aside:
            pdf.set_font("Helvetica", "", 8.5)
            pdf.set_text_color(*MUTED)
            pdf.cell(40, 7, aside, align="R")
        pdf.set_draw_color(*LINE)
        pdf.line(MARGIN, y + 9, MARGIN + pdf.epw, y + 9)
        pdf.set_xy(MARGIN, y + 12)

    @staticmethod
    def _subheading(pdf: FPDF, text: str):
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*MUTED)
        pdf.cell(0, 6, text.upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def _findings(self, pdf: FPDF, items: list, level_key: str, title_key: str, text_key: str, empty: str):
        """Severity tag on the left, title and explanation on the right."""
        if not items:
            self._text(pdf, empty, size=9.5, color=TONE_COLORS["stable"])
            return
        for item in items:
            level = str(item.get(level_key, "low")).lower()
            y = pdf.get_y()
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*LEVEL_COLORS.get(level, MUTED))
            pdf.cell(20, 5.2, level.capitalize())
            pdf.set_xy(MARGIN + 20, y)
            pdf.set_font("Helvetica", "B", 9.5)
            pdf.set_text_color(*INK)
            pdf.multi_cell(pdf.epw - 20, 5.2, str(item.get(title_key, "")), align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_x(MARGIN + 20)
            pdf.set_font("Helvetica", "", 9.5)
            pdf.set_text_color(*MUTED)
            pdf.multi_cell(pdf.epw - 20, 4.8, str(item.get(text_key, "")), align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1.5)

    # ── Sections ─────────────────────────────────────────────────

    def _header(self, pdf: FPDF, data: dict):
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*ACCENT)
        pdf.cell(12, 5, "ARIA")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*MUTED)
        pdf.cell(0, 5, "Financial risk analysis", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1)
        self._text(pdf, data.get("company") or "Unknown company", size=20, style="B", height=9)
        analyzed = format_timestamp(data.get("timestamp"))
        meta = [f"Analyzed {analyzed}" if analyzed else "", f"Report ID {data.get('doc_id', '')}"]
        self._text(pdf, "  |  ".join(m for m in meta if m), size=9, color=MUTED)
        if data.get("fallback_model"):
            self._text(pdf, f"Analyzed with the backup AI model ({data['fallback_model']}) because the main model "
                            "was at its usage limit.", size=8.5, color=TONE_COLORS["elevated"])

    def _score(self, pdf: FPDF, data: dict):
        score = int(data.get("overall_risk_score", 0))
        tone = TONE_COLORS[score_tone(score)]
        breakdown = data.get("score_breakdown") or {
            # Analyses saved before the breakdown existed: show the raw 0-50 sub-scores
            "financial": data.get("financial_signals", {}).get("financial_risk_score", 0), "financial_max": 50,
            "news": data.get("news_signals", {}).get("news_risk_score", 0), "news_max": 50,
        }

        pdf.ln(4)
        top, height = pdf.get_y(), 32
        pdf.set_draw_color(*LINE)
        pdf.rect(MARGIN, top, pdf.epw, height, style="D", round_corners=True, corner_radius=2.5)

        pdf.set_xy(MARGIN + 6, top + 5)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*MUTED)
        pdf.cell(40, 5, "Risk score")
        pdf.set_xy(MARGIN + 6, top + 11)
        pdf.set_font("Helvetica", "B", 30)
        pdf.set_text_color(*tone)
        pdf.cell(pdf.get_string_width(str(score)) + 1, 12, str(score))
        pdf.set_font("Helvetica", "", 12)
        pdf.set_text_color(*MUTED)
        pdf.cell(15, 14, "/100")
        pdf.set_xy(MARGIN + 6, top + 23)
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_text_color(*tone)
        pdf.cell(40, 5, rating_label(data.get("rating", "")))

        # Breakdown bars on the right
        left, width = MARGIN + 62, pdf.epw - 68
        for i, (label, key) in enumerate([("Financial statements", "financial"), ("Recent news", "news")]):
            value, maximum = breakdown.get(key, 0), breakdown.get(f"{key}_max", 1) or 1
            y = top + 5 + i * 10
            pdf.set_xy(left, y)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*MUTED)
            pdf.cell(width - 20, 5, label)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*INK)
            pdf.cell(20, 5, f"{value} / {maximum}", align="R")
            pdf.set_fill_color(*SUBTLE)
            pdf.rect(left, y + 6, width, 1.6, style="F")
            if value > 0:  # a zero-width rect still renders as a hairline
                pdf.set_fill_color(*ACCENT)
                pdf.rect(left, y + 6, width * min(value / maximum, 1), 1.6, style="F")
        pdf.set_xy(left, top + 25)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(*MUTED)
        pdf.cell(width, 4, "Higher is riskier. 0-40 low, 41-70 medium, 71-100 critical.")
        pdf.set_xy(MARGIN, top + height)

    def _financials(self, pdf: FPDF, fin: dict):
        self._section_title(pdf, "Financial statements")
        if fin.get("summary"):
            self._text(pdf, fin["summary"], size=9.5, color=MUTED)

        metrics = fin.get("key_metrics") or []
        if metrics:
            pdf.ln(3)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*INK)
            pdf.set_draw_color(*LINE)
            pdf.set_fill_color(255, 255, 255)  # the table fills cells with the current color
            with pdf.table(
                col_widths=(60, 42, 42, 30),
                text_align=("LEFT", "LEFT", "LEFT", "RIGHT"),
                borders_layout="HORIZONTAL_LINES",
                headings_style=FontFace(emphasis="BOLD", color=MUTED, fill_color=SUBTLE),
                line_height=5,
                padding=1.2,
            ) as table:
                for row_values in [("Metric", "Current", "Prior", "Change")] + [
                    (m.get("metric", ""), m.get("current", ""), m.get("prior", ""), m.get("change", "")) for m in metrics
                ]:
                    row = table.row()
                    for value in row_values:
                        row.cell(str(value))

        self._subheading(pdf, "Adverse changes")
        self._findings(pdf, fin.get("anomalies") or [], "severity", "metric", "observation",
                       "No adverse changes found in the statements.")

    def _news(self, pdf: FPDF, news: dict):
        self._section_title(pdf, "Recent news", f"Last {news.get('window_days') or 30} days")
        if news.get("available") is False:
            self._text(pdf, "News couldn't be fetched, so this score is based on the document only.",
                       size=9.5, color=TONE_COLORS["elevated"])
            return
        if news.get("summary"):
            self._text(pdf, news["summary"], size=9.5, color=MUTED)

        self._subheading(pdf, "Risk signals")
        self._findings(pdf, news.get("signals") or [], "impact", "signal", "description",
                       "No material risks in recent news.")

        stories = news.get("top_stories") or []
        if stories:
            self._subheading(pdf, "Sources")
            for story in stories:
                pdf.set_font("Helvetica", "U", 9.5)
                pdf.set_text_color(*ACCENT)
                pdf.multi_cell(0, 5, story.get("title", ""), link=story.get("url", ""), align="L",
                               new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                published = format_date(story.get("published_at"))
                self._text(pdf, " | ".join(p for p in [story.get("source", ""), published] if p), size=8, color=MUTED, height=4.5)
                pdf.ln(0.8)

    # ── Public API ───────────────────────────────────────────────

    def generate_pdf_report(self, report_data: dict) -> str:
        """Build the PDF for an analysis (same content as the dashboard) and return its path."""
        pdf = ReportPDF(format="A4")
        pdf.set_title(to_pdf_text(f"ARIA risk analysis - {report_data.get('company', '')}"))
        pdf.set_margins(MARGIN, MARGIN, MARGIN)
        pdf.set_auto_page_break(auto=True, margin=18)
        pdf.add_page()

        self._header(pdf, report_data)
        self._score(pdf, report_data)
        self._financials(pdf, report_data.get("financial_signals") or {})
        self._news(pdf, report_data.get("news_signals") or {})

        # Company names come from the LLM and may contain "/", ":" etc. — keep the filename path-safe
        company = to_pdf_text(str(report_data.get("company") or ""))
        ascii_company = unicodedata.normalize("NFKD", company).encode("ascii", "ignore").decode()
        safe_company = re.sub(r"[^A-Za-z0-9_-]+", "_", ascii_company).strip("_") or "Company"
        safe_doc_id = re.sub(r"[^A-Za-z0-9_-]+", "_", str(report_data.get("doc_id", "Unknown")))
        file_path = self.output_dir / f"ARIA_Report_{safe_company}_{safe_doc_id}.pdf"
        pdf.output(str(file_path))
        return str(file_path)
