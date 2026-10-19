"use client"

import { useState } from 'react';
import { Loader2, MessageSquare } from 'lucide-react';
import { api, getErrorMessage } from '@/lib/api';
import type { QueryAnswer } from '@/lib/types';

interface Exchange {
    question: string;
    result?: QueryAnswer;
    error?: string;
}

const SUGGESTIONS = ['What was total revenue?', 'How much debt does the company have?', 'What are the main risk factors?'];

export default function AskPanel({ docId, company }: { docId: string; company: string }) {
    const [question, setQuestion] = useState('');
    const [history, setHistory] = useState<Exchange[]>([]);
    const [asking, setAsking] = useState(false);

    const ask = async (text: string) => {
        const q = text.trim();
        if (!q || asking) return;
        setAsking(true);
        setQuestion('');
        try {
            const result = await api.queryDocument(docId, q);
            setHistory((h) => [{ question: q, result }, ...h]);
        } catch (err) {
            setHistory((h) => [{ question: q, error: getErrorMessage(err) }, ...h]);
        } finally {
            setAsking(false);
        }
    };

    return (
        <section className="card" aria-labelledby="ask-title">
            <header className="flex items-center gap-2 border-b border-line px-5 py-4">
                <MessageSquare className="h-4 w-4 text-muted" aria-hidden />
                <h2 id="ask-title" className="section-title">Ask about this report</h2>
            </header>

            <div className="space-y-4 p-5">
                <form
                    className="flex gap-2"
                    onSubmit={(e) => {
                        e.preventDefault();
                        ask(question);
                    }}
                >
                    <label htmlFor="ask-input" className="sr-only">Question about {company}</label>
                    <input
                        id="ask-input"
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        placeholder={`Ask a question about ${company}'s report`}
                        className="min-w-0 flex-1 rounded-lg border border-line bg-surface px-3 py-2 text-sm placeholder:text-muted focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20"
                    />
                    <button type="submit" className="btn-primary" disabled={asking || !question.trim()}>
                        {asking ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : 'Ask'}
                    </button>
                </form>

                {history.length === 0 && (
                    <div className="flex flex-wrap gap-2">
                        {SUGGESTIONS.map((s) => (
                            <button key={s} onClick={() => ask(s)} disabled={asking} className="rounded-full border border-line px-3 py-1 text-xs text-muted hover:bg-subtle hover:text-ink disabled:opacity-50">
                                {s}
                            </button>
                        ))}
                    </div>
                )}

                {history.map((ex, i) => (
                    <div key={history.length - i} className="space-y-2 border-t border-line pt-4 first:border-t-0 first:pt-0">
                        <p className="text-sm font-medium">{ex.question}</p>
                        {ex.error ? (
                            <p className="text-sm text-risk-critical">{ex.error}</p>
                        ) : (
                            <>
                                <p className="whitespace-pre-line text-sm leading-relaxed text-muted">{ex.result?.answer}</p>
                                {!!ex.result?.sources.length && (
                                    <details className="text-xs text-muted">
                                        <summary className="cursor-pointer select-none hover:text-ink">
                                            Show {ex.result.sources.length} source excerpts
                                        </summary>
                                        <ul className="mt-2 space-y-2">
                                            {ex.result.sources.map((src, j) => (
                                                <li key={j} className="rounded-md bg-subtle p-2.5 leading-relaxed">
                                                    {src.length > 400 ? `${src.slice(0, 400)}…` : src}
                                                </li>
                                            ))}
                                        </ul>
                                    </details>
                                )}
                            </>
                        )}
                    </div>
                ))}
            </div>
        </section>
    );
}
