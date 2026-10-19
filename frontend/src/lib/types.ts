// Shapes returned by the ARIA backend (see backend/models/schemas.py)

export type Level = 'high' | 'medium' | 'low';

export interface KeyMetric {
    metric: string;
    current: string;
    prior: string;
    change: string;
}

export interface Anomaly {
    metric: string;
    observation: string;
    severity: Level;
}

export interface NewsSignal {
    signal: string;
    impact: Level;
    description: string;
}

export interface Story {
    title: string;
    url: string;
    source: string;
    published_at?: string | null;
}

export interface ScoreBreakdown {
    financial: number;
    financial_max: number;
    news: number;
    news_max: number;
}

export interface RiskReport {
    doc_id: string;
    company: string;
    overall_risk_score: number;
    rating: string;
    // Older saved analyses don't have the fields below
    score_breakdown?: ScoreBreakdown | null;
    financial_signals: {
        financial_risk_score: number;
        key_metrics?: KeyMetric[];
        anomalies: Anomaly[];
        summary: string;
    };
    news_signals: {
        news_risk_score: number;
        summary: string;
        signals: NewsSignal[];
        top_stories?: Story[] | null;
        available?: boolean;
        window_days?: number | null;
    };
    timestamp: string;
    // Set when the main AI model was out of quota and the backup model answered
    fallback_model?: string | null;
}

export interface DocumentSummary {
    doc_id: string;
    company: string | null;
    uploaded_at: string;
    chunks: number;
}

export interface QueryAnswer {
    answer: string;
    sources: string[];
    chunks_searched: number;
}
