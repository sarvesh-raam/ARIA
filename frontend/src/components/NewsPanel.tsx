import { AlertTriangle, ArrowUpRight, CheckCircle2, Newspaper } from 'lucide-react';
import LevelBadge from './LevelBadge';
import { formatDate } from '@/lib/format';
import type { RiskReport } from '@/lib/types';

export default function NewsPanel({ data }: { data: RiskReport['news_signals'] }) {
    const stories = data.top_stories ?? [];
    const windowDays = data.window_days ?? 30;

    return (
        <section className="card" aria-labelledby="news-title">
            <header className="flex items-center justify-between gap-2 border-b border-line px-5 py-4">
                <div className="flex items-center gap-2">
                    <Newspaper className="h-4 w-4 text-muted" aria-hidden />
                    <h2 id="news-title" className="section-title">Recent news</h2>
                </div>
                <span className="text-xs text-muted">Last {windowDays} days</span>
            </header>

            <div className="space-y-5 p-5">
                {data.available === false ? (
                    <p className="flex items-start gap-2 text-sm text-risk-elevated">
                        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
                        News couldn&apos;t be fetched, so this score is based on the document only.
                    </p>
                ) : (
                    <>
                        {data.summary && <p className="text-sm leading-relaxed text-muted">{data.summary}</p>}

                        <div>
                            <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">Risk signals</h3>
                            {data.signals.length === 0 ? (
                                <p className="flex items-center gap-2 text-sm text-risk-stable">
                                    <CheckCircle2 className="h-4 w-4" aria-hidden /> No material risks in recent news.
                                </p>
                            ) : (
                                <ul className="space-y-3">
                                    {data.signals.map((s, i) => (
                                        <li key={i} className="flex gap-3">
                                            <LevelBadge level={s.impact} />
                                            <div className="min-w-0 text-sm">
                                                <p className="font-medium">{s.signal}</p>
                                                <p className="mt-0.5 leading-relaxed text-muted">{s.description}</p>
                                            </div>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>

                        {stories.length > 0 && (
                            <div>
                                <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">Sources</h3>
                                <ul className="divide-y divide-line rounded-lg border border-line">
                                    {stories.map((story) => (
                                        <li key={story.url}>
                                            <a
                                                href={story.url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="group flex items-start justify-between gap-3 px-3 py-2.5 text-sm hover:bg-subtle"
                                            >
                                                <span className="min-w-0">
                                                    <span className="line-clamp-2 group-hover:underline">{story.title}</span>
                                                    <span className="mt-0.5 block text-xs text-muted">
                                                        {story.source}
                                                        {story.published_at ? ` · ${formatDate(story.published_at)}` : ''}
                                                    </span>
                                                </span>
                                                <ArrowUpRight className="mt-0.5 h-4 w-4 shrink-0 text-muted" aria-hidden />
                                            </a>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </>
                )}
            </div>
        </section>
    );
}
