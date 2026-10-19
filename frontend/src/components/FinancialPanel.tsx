import { CheckCircle2, FileText } from 'lucide-react';
import LevelBadge from './LevelBadge';
import type { RiskReport } from '@/lib/types';

export default function FinancialPanel({ data }: { data: RiskReport['financial_signals'] }) {
    const metrics = data.key_metrics ?? [];

    return (
        <section className="card" aria-labelledby="financial-title">
            <header className="flex items-center gap-2 border-b border-line px-5 py-4">
                <FileText className="h-4 w-4 text-muted" aria-hidden />
                <h2 id="financial-title" className="section-title">Financial statements</h2>
            </header>

            <div className="space-y-5 p-5">
                {data.summary && <p className="text-sm leading-relaxed text-muted">{data.summary}</p>}

                {metrics.length > 0 && (
                    <div className="-mx-5 overflow-x-auto">
                        <table className="w-full min-w-[480px] text-sm">
                            <thead>
                                <tr className="border-y border-line bg-subtle/60 text-left text-xs text-muted">
                                    <th className="px-5 py-2 font-medium">Metric</th>
                                    <th className="px-3 py-2 font-medium">Current</th>
                                    <th className="px-3 py-2 font-medium">Prior</th>
                                    <th className="px-5 py-2 text-right font-medium">Change</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-line">
                                {metrics.map((m) => (
                                    <tr key={m.metric}>
                                        <td className="px-5 py-2.5 font-medium">{m.metric}</td>
                                        <td className="px-3 py-2.5 tabular-nums">{m.current}</td>
                                        <td className="px-3 py-2.5 tabular-nums text-muted">{m.prior}</td>
                                        <td className="px-5 py-2.5 text-right tabular-nums">{m.change}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                <div>
                    <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">Adverse changes</h3>
                    {data.anomalies.length === 0 ? (
                        <p className="flex items-center gap-2 text-sm text-risk-stable">
                            <CheckCircle2 className="h-4 w-4" aria-hidden /> No adverse changes found in the statements.
                        </p>
                    ) : (
                        <ul className="space-y-3">
                            {data.anomalies.map((a, i) => (
                                <li key={i} className="flex gap-3">
                                    <LevelBadge level={a.severity} />
                                    <div className="min-w-0 text-sm">
                                        <p className="font-medium">{a.metric}</p>
                                        <p className="mt-0.5 leading-relaxed text-muted">{a.observation}</p>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </div>
        </section>
    );
}
