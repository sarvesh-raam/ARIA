import { Loader2 } from 'lucide-react';

export default function ProgressView({ status, progress }: { status: string; progress: number }) {
    return (
        <div className="mx-auto max-w-md py-24 text-center" role="status" aria-live="polite">
            <Loader2 className="mx-auto h-6 w-6 animate-spin text-accent" aria-hidden />
            <p className="mt-4 text-sm font-medium">{status || 'Working…'}</p>
            <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-subtle">
                <div className="h-full rounded-full bg-accent transition-[width] duration-500" style={{ width: `${progress}%` }} />
            </div>
            <p className="mt-3 text-xs text-muted">Large annual reports can take a few minutes.</p>
        </div>
    );
}
