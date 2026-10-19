from pydantic import BaseModel
from typing import Optional


class QueryRequest(BaseModel):
    """Request body for POST /api/query"""
    doc_id: str
    question: str


class DocumentInfo(BaseModel):
    """Metadata stored per uploaded document"""
    doc_id: str
    filename: str
    company: Optional[str] = "Unknown"
    uploaded_at: str
    chunks: int
    preview: Optional[str] = None


class QueryResponse(BaseModel):
    """Response from POST /api/query"""
    answer: str
    sources: list[str]
    chunks_searched: int


class UploadResponse(BaseModel):
    """Response from POST /api/upload"""
    doc_id: str
    filename: str
    company: Optional[str]
    status: str
    message: str
    chunks: int
    preview: Optional[str] = None


# ── Phase 2: Risk Analysis ─────────────────────────────────────

class RiskSignal(BaseModel):
    signal: str
    impact: str
    description: str


class FinancialAnalysis(BaseModel):
    financial_risk_score: int
    key_metrics: list[dict] = []
    anomalies: list[dict]
    summary: str
    model: Optional[str] = None


class NewsAnalysis(BaseModel):
    news_risk_score: int
    summary: str
    model: Optional[str] = None
    signals: list[RiskSignal]
    top_stories: Optional[list[dict]] = None
    available: bool = True  # False when news could not be fetched
    window_days: Optional[int] = None


class RiskReport(BaseModel):
    doc_id: str
    company: str
    overall_risk_score: int
    rating: str
    score_breakdown: Optional[dict] = None
    financial_signals: FinancialAnalysis
    news_signals: NewsAnalysis
    timestamp: str
    fallback_model: Optional[str] = None
