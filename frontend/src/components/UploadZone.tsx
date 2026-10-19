"use client"

import { useState } from 'react';
import { Upload } from 'lucide-react';

const STEPS = [
    ['Reads the statements', 'Finds the income statement, balance sheet and cash flow statement in your PDF.'],
    ['Checks recent news', 'Looks for lawsuits, regulatory action and other risks from the last 30 days.'],
    ['Scores the risk', 'Combines both into a 0–100 score with every finding traced to its source.'],
];

export default function UploadZone({ onFile, disabled }: { onFile: (file: File) => void; disabled?: boolean }) {
    const [dragging, setDragging] = useState(false);

    return (
        <div className="mx-auto max-w-2xl py-8 sm:py-16">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Analyze a financial report</h1>
            <p className="mt-2 text-muted">
                Upload an annual report, 10-K, 10-Q or results press release to get a risk assessment.
            </p>

            <label
                onDragOver={(e) => {
                    e.preventDefault();
                    setDragging(true);
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={(e) => {
                    e.preventDefault();
                    setDragging(false);
                    const file = e.dataTransfer.files?.[0];
                    if (file && !disabled) onFile(file);
                }}
                className={`mt-8 flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-12 text-center transition-colors ${
                    dragging ? 'border-accent bg-accent/5' : 'border-line bg-surface hover:border-accent/50'
                }`}
            >
                <input
                    type="file"
                    accept=".pdf,application/pdf"
                    className="sr-only"
                    disabled={disabled}
                    onChange={(e) => {
                        const file = e.target.files?.[0];
                        // Reset so choosing the same file again still triggers onChange
                        e.target.value = '';
                        if (file) onFile(file);
                    }}
                />
                <span className="flex h-10 w-10 items-center justify-center rounded-full bg-accent/10 text-accent">
                    <Upload className="h-5 w-5" aria-hidden />
                </span>
                <span className="mt-3 text-sm font-medium">Drop a PDF here or click to choose a file</span>
                <span className="mt-1 text-xs text-muted">Text-based PDF, up to 25 MB</span>
            </label>
            <p className="mt-3 text-xs leading-relaxed text-muted">
                Your uploads are private to this browser and are deleted when the server restarts.
                Avoid uploading highly sensitive documents to this demo.
            </p>

            <ol className="mt-10 grid gap-6 sm:grid-cols-3">
                {STEPS.map(([title, text], i) => (
                    <li key={title}>
                        <span className="text-xs font-medium text-accent">Step {i + 1}</span>
                        <p className="mt-1 text-sm font-medium">{title}</p>
                        <p className="mt-1 text-sm leading-relaxed text-muted">{text}</p>
                    </li>
                ))}
            </ol>
        </div>
    );
}
