import { ChevronRight, FileText } from 'lucide-react';
import { formatDateTime } from '@/lib/format';
import type { DocumentSummary } from '@/lib/types';

export default function HistoryList({ docs, onOpen }: { docs: DocumentSummary[]; onOpen: (doc: DocumentSummary) => void }) {
    const sorted = [...docs].sort((a, b) => b.uploaded_at.localeCompare(a.uploaded_at));

    return (
        <div className="mx-auto max-w-3xl">
            <h1 className="text-xl font-semibold tracking-tight">History</h1>
            <p className="mt-1 text-sm text-muted">Reports you uploaded from this browser. Open one to see its last analysis.</p>

            {sorted.length === 0 ? (
                <div className="card mt-6 px-6 py-12 text-center">
                    <FileText className="mx-auto h-6 w-6 text-muted" aria-hidden />
                    <p className="mt-3 text-sm font-medium">No reports yet</p>
                    <p className="mt-1 text-sm text-muted">Reports you upload from this browser will appear here.</p>
                </div>
            ) : (
                <ul className="card mt-6 divide-y divide-line overflow-hidden">
                    {sorted.map((doc) => (
                        <li key={doc.doc_id}>
                            <button onClick={() => onOpen(doc)} className="flex w-full items-center gap-4 px-5 py-4 text-left hover:bg-subtle">
                                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-subtle text-muted">
                                    <FileText className="h-4 w-4" aria-hidden />
                                </span>
                                <span className="min-w-0 flex-1">
                                    <span className="block truncate text-sm font-medium">{doc.company || 'Unknown company'}</span>
                                    <span className="block text-xs text-muted">
                                        Uploaded {formatDateTime(doc.uploaded_at)} · {doc.chunks} sections indexed
                                    </span>
                                </span>
                                <ChevronRight className="h-4 w-4 shrink-0 text-muted" aria-hidden />
                            </button>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}
