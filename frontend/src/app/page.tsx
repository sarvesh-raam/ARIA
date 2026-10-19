"use client"

import { useEffect, useState } from 'react';
import { AlertTriangle, Download, Loader2, RefreshCw, Shield, Upload, X } from 'lucide-react';
import { api, API_BASE_URL, getErrorMessage, isNotFound, newTaskId } from '@/lib/api';
import { formatDateTime } from '@/lib/format';
import type { DocumentSummary, RiskReport } from '@/lib/types';
import AskPanel from '@/components/AskPanel';
import FinancialPanel from '@/components/FinancialPanel';
import HistoryList from '@/components/HistoryList';
import NewsPanel from '@/components/NewsPanel';
import ProgressView from '@/components/ProgressView';
import ScoreCard from '@/components/ScoreCard';
import UploadZone from '@/components/UploadZone';

type View = 'analyze' | 'history';

function StatusPill({ latency }: { latency: number | null }) {
    const online = latency !== null && latency >= 0;
    const label = latency === null ? 'Connecting' : online ? `Online · ${latency} ms` : 'Offline';
    const dot = latency === null ? 'bg-muted' : online ? 'bg-risk-stable' : 'bg-risk-critical';
    return (
        <span className="hidden items-center gap-2 rounded-full border border-line px-2.5 py-1 text-xs text-muted sm:inline-flex" title="Backend status">
            <span className={`h-1.5 w-1.5 rounded-full ${dot}`} aria-hidden />
            {label}
        </span>
    );
}

export default function Dashboard() {
    const [view, setView] = useState<View>('analyze');
    const [report, setReport] = useState<RiskReport | null>(null);
    // Opened from history but never analyzed (or its analysis was lost on a server restart)
    const [unanalyzed, setUnanalyzed] = useState<DocumentSummary | null>(null);
    const [busy, setBusy] = useState(false);
    const [downloading, setDownloading] = useState(false);
    const [status, setStatus] = useState('');
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [history, setHistory] = useState<DocumentSummary[]>([]);
    // null = not checked yet, -1 = unreachable, otherwise round-trip ms
    const [latency, setLatency] = useState<number | null>(null);

    const fetchHistory = () => api.listDocuments().then(setHistory).catch((err) => console.error('Failed to fetch history', err));

    useEffect(() => {
        fetchHistory();
        const checkBackend = () => api.ping().then(setLatency).catch(() => setLatency(-1));
        checkBackend();
        const timer = setInterval(checkBackend, 30000);
        return () => clearInterval(timer);
    }, []);

    // Follow a backend task's progress; closes itself at 100% or if the stream errors
    const trackProgress = (progressId: string) => {
        const source = new EventSource(`${API_BASE_URL}/api/progress/${progressId}`);
        source.onmessage = (event) => {
            const data = JSON.parse(event.data);
            setProgress(data.percentage);
            setStatus(data.status);
            if (data.percentage >= 100) source.close();
        };
        source.onerror = () => source.close();
        return source;
    };

    // Run a step with the progress screen; on failure show the backend's message
    const withProgress = async (initialStatus: string, work: (sources: EventSource[]) => Promise<void>) => {
        setBusy(true);
        setError(null);
        setView('analyze');
        setProgress(0);
        setStatus(initialStatus);
        const sources: EventSource[] = [];
        try {
            await work(sources);
        } catch (err) {
            console.error(err);
            setError(getErrorMessage(err));
        } finally {
            sources.forEach((s) => s.close());
            setBusy(false);
            setStatus('');
        }
    };

    const analyze = (docId: string, sources: EventSource[]) => {
        // Fresh progress ID per run, so the stream can't pick up the last run's "complete"
        const taskId = newTaskId();
        sources.push(trackProgress(taskId));
        return api.analyzeDocument(docId, taskId).then((result) => {
            setReport(result);
            setUnanalyzed(null);
        });
    };

    const handleFile = (file: File) =>
        withProgress('Uploading report…', async (sources) => {
            setReport(null);
            setUnanalyzed(null);
            const taskId = newTaskId();
            sources.push(trackProgress(taskId));
            const upload = await api.uploadDocument(file, taskId);
            sources.forEach((s) => s.close());
            await analyze(upload.doc_id, sources);
            fetchHistory();
        });

    const downloadPdf = async (docId: string) => {
        setDownloading(true);
        setError(null);
        try {
            await api.downloadReport(docId);
        } catch (err) {
            setError(getErrorMessage(err));
        } finally {
            setDownloading(false);
        }
    };

    const rerun = (docId: string) => withProgress('Starting analysis…', (sources) => analyze(docId, sources));

    const openDocument = async (doc: DocumentSummary) => {
        setError(null);
        setView('analyze');
        try {
            setReport(await api.getAnalysis(doc.doc_id));
            setUnanalyzed(null);
        } catch (err) {
            if (isNotFound(err)) {
                setReport(null);
                setUnanalyzed(doc);
            } else {
                setError(getErrorMessage(err));
            }
        }
    };

    const tabClass = (tab: View) =>
        `relative px-1 py-4 text-sm font-medium transition-colors ${
            view === tab ? 'text-ink after:absolute after:inset-x-0 after:bottom-0 after:h-0.5 after:bg-accent' : 'text-muted hover:text-ink'
        }`;

    return (
        <div className="flex min-h-screen flex-col">
            <header className="sticky top-0 z-10 border-b border-line bg-surface/90 backdrop-blur">
                <div className="mx-auto flex max-w-6xl items-center gap-6 px-4 sm:px-6">
                    <div className="flex items-center gap-2">
                        <span className="flex h-7 w-7 items-center justify-center rounded-md bg-accent text-on-accent">
                            <Shield className="h-4 w-4" aria-hidden />
                        </span>
                        <span className="text-sm font-semibold tracking-tight">ARIA</span>
                    </div>

                    <nav className="flex gap-5" aria-label="Main">
                        <button className={tabClass('analyze')} onClick={() => setView('analyze')}>Analyze</button>
                        <button className={tabClass('history')} onClick={() => { setView('history'); fetchHistory(); }}>History</button>
                    </nav>

                    <div className="ml-auto flex items-center gap-3">
                        <StatusPill latency={latency} />
                        <label className={`btn-primary cursor-pointer ${busy ? 'pointer-events-none opacity-50' : ''}`}>
                            <input
                                type="file"
                                accept=".pdf,application/pdf"
                                className="sr-only"
                                disabled={busy}
                                onChange={(e) => {
                                    const file = e.target.files?.[0];
                                    e.target.value = '';
                                    if (file) handleFile(file);
                                }}
                            />
                            <Upload className="h-4 w-4" aria-hidden />
                            <span className="hidden sm:inline">Upload report</span>
                        </label>
                    </div>
                </div>
            </header>

            <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-6 sm:py-8">
                {error && !busy && (
                    <div role="alert" className="mb-6 flex items-start gap-3 rounded-xl border border-risk-critical/30 bg-risk-critical/5 p-4">
                        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-risk-critical" aria-hidden />
                        <div className="flex-1 text-sm">
                            <p className="font-medium">Analysis failed</p>
                            <p className="mt-0.5 text-muted">{error}</p>
                        </div>
                        <button onClick={() => setError(null)} className="text-muted hover:text-ink" aria-label="Dismiss">
                            <X className="h-4 w-4" />
                        </button>
                    </div>
                )}

                {view === 'history' ? (
                    <HistoryList docs={history} onOpen={openDocument} />
                ) : busy ? (
                    <ProgressView status={status} progress={progress} />
                ) : report ? (
                    <div className="space-y-6">
                        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                            <div className="min-w-0">
                                <h1 className="truncate text-2xl font-semibold tracking-tight">{report.company}</h1>
                                <p className="mt-1 text-sm text-muted">Analyzed {formatDateTime(report.timestamp)}</p>
                            </div>
                            <div className="flex gap-2">
                                <button onClick={() => rerun(report.doc_id)} className="btn-secondary">
                                    <RefreshCw className="h-4 w-4" aria-hidden /> Re-run
                                </button>
                                <button onClick={() => downloadPdf(report.doc_id)} disabled={downloading} className="btn-secondary">
                                    {downloading
                                        ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                                        : <Download className="h-4 w-4" aria-hidden />}
                                    Download PDF
                                </button>
                            </div>
                        </div>

                        <ScoreCard report={report} />

                        <div className="grid gap-6 lg:grid-cols-2 [&>*]:min-w-0">
                            <FinancialPanel data={report.financial_signals} />
                            <NewsPanel data={report.news_signals} />
                        </div>

                        <AskPanel docId={report.doc_id} company={report.company} />
                    </div>
                ) : unanalyzed ? (
                    <div className="card mx-auto max-w-lg px-6 py-10 text-center">
                        <p className="text-sm font-medium">{unanalyzed.company || 'This report'} has no saved analysis</p>
                        <p className="mt-1 text-sm text-muted">It may not have been analyzed yet, or the server was restarted since.</p>
                        <button onClick={() => rerun(unanalyzed.doc_id)} className="btn-primary mt-5">Run analysis</button>
                    </div>
                ) : (
                    <UploadZone onFile={handleFile} disabled={busy} />
                )}
            </main>

            <footer className="border-t border-line">
                <p className="mx-auto max-w-6xl px-4 py-4 text-xs text-muted sm:px-6">
                    AI-generated analysis for information only. Verify figures against the source document before relying on them.
                </p>
            </footer>
        </div>
    );
}
