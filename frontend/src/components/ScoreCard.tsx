import { ratingLabel, scoreTone, type Tone } from '@/lib/format';
import type { RiskReport } from '@/lib/types';

const TONE_TEXT: Record<Tone, string> = {
    stable: 'text-risk-stable',
    elevated: 'text-risk-elevated',
    critical: 'text-risk-critical',
};

const TONE_PILL: Record<Tone, string> = {
    stable: 'bg-risk-stable/10 text-risk-stable',
    elevated: 'bg-risk-elevated/10 text-risk-elevated',
    critical: 'bg-risk-critical/10 text-risk-critical',
};

function BreakdownBar({ label, value, max }: { label: string; value: number; max: number }) {
    return (
        <div>
            <div className="mb-1.5 flex items-baseline justify-between text-sm">
                <span className="text-muted">{label}</span>
                <span className="font-medium tabular-nums">
                    {value}<span className="text-muted"> / {max}</span>
                </span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-subtle">
                <div className="h-full rounded-full bg-accent" style={{ width: `${max ? (value / max) * 100 : 0}%` }} />
            </div>
        </div>
    );
}

export default function ScoreCard({ report }: { report: RiskReport }) {
    const tone = scoreTone(report.overall_risk_score);
    const breakdown = report.score_breakdown;

    return (
        <section className="card p-5 sm:p-6" aria-label="Risk score">
            <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:gap-10">
                <div className="shrink-0">
                    <p className="text-sm text-muted">Risk score</p>
                    <p className="mt-1 flex items-baseline gap-1">
                        <span className={`text-5xl font-semibold tabular-nums tracking-tight ${TONE_TEXT[tone]}`}>
                            {report.overall_risk_score}
                        </span>
                        <span className="text-lg text-muted">/100</span>
                    </p>
                    <span className={`mt-2 inline-flex rounded-md px-2 py-0.5 text-sm font-medium ${TONE_PILL[tone]}`}>
                        {ratingLabel(report.rating)}
                    </span>
                </div>

                <div className="flex-1 space-y-4">
                    {breakdown ? (
                        <>
                            <BreakdownBar label="Financial statements" value={breakdown.financial} max={breakdown.financial_max} />
                            <BreakdownBar label="Recent news" value={breakdown.news} max={breakdown.news_max} />
                        </>
                    ) : (
                        <>
                            <BreakdownBar label="Financial statements" value={report.financial_signals.financial_risk_score} max={50} />
                            <BreakdownBar label="Recent news" value={report.news_signals.news_risk_score} max={50} />
                        </>
                    )}
                    <p className="text-xs text-muted">Higher is riskier. 0–40 low, 41–70 medium, 71–100 critical.</p>
                </div>
            </div>
        </section>
    );
}
