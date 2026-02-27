"use client"

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Shield,
    Upload,
    FileText,
    TrendingDown,
    AlertTriangle,
    CheckCircle,
    Globe,
    Download,
    Loader2,
    ChevronRight,
    Plus
} from 'lucide-react';
import { api } from '@/lib/api';

export default function Dashboard() {
    const [file, setFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState("");
    const [progress, setProgress] = useState(0);
    const [report, setReport] = useState<any>(null);
    const [history, setHistory] = useState<any[]>([]);

    // Load history on mount
    useEffect(() => {
        fetchHistory();
    }, []);

    const fetchHistory = async () => {
        try {
            const docs = await api.listDocuments();
            setHistory(docs);
        } catch (err) {
            console.error("Failed to fetch history", err);
        }
    };

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const selected = e.target.files?.[0];
        if (!selected) return;

        setLoading(true);
        setReport(null);
        setProgress(0);
        try {
            setStatus("Initializing...");
            const tempTaskId = "task_" + Math.random().toString(36).substring(7);

            // Start listening to SSE for progress BEFORE uploading
            const eventSource = new EventSource(`http://localhost:8000/api/progress/${tempTaskId}`);
            eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                setProgress(data.percentage);
                setStatus(data.status);
            };

            const uploadRes = await api.uploadDocument(selected, tempTaskId);
            const docId = uploadRes.doc_id;

            // Close old listener and start new one for the final docId (analysis phase)
            eventSource.close();
            const analysisSource = new EventSource(`http://localhost:8000/api/progress/${docId}`);
            analysisSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                setProgress(data.percentage);
                setStatus(data.status);
                if (data.percentage >= 100) analysisSource.close();
            };

            const analysisRes = await api.analyzeDocument(docId);

            setReport(analysisRes);
            fetchHistory();
            analysisSource.close();
        } catch (err) {
            console.error(err);
            alert("Analysis failed. Please check backend connection.");
        } finally {
            setLoading(false);
            setStatus("");
        }
    };

    return (
        <main className="min-h-screen bg-background text-foreground selection:bg-purple/30 p-4 md:p-8">
            {/* Background Glow */}
            <div className="fixed top-0 left-1/4 w-[500px] h-[500px] bg-purple/10 rounded-full blur-[120px] pointer-events-none -z-10" />
            <div className="fixed bottom-0 right-1/4 w-[400px] h-[400px] bg-blue-500/5 rounded-full blur-[100px] pointer-events-none -z-10" />

            <div className="max-w-7xl mx-auto space-y-8">
                {/* Header */}
                <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-gradient-to-br from-purple to-purple-dark rounded-xl shadow-lg shadow-purple/20">
                            <Shield className="w-8 h-8 text-white" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold tracking-tight">ARIA</h1>
                            <p className="text-foreground/50 text-sm">Autonomous Risk Intelligence Agent</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="hidden md:flex flex-col items-end">
                            <span className="text-xs text-foreground/40 uppercase tracking-widest font-bold">System Status</span>
                            <span className="text-xs text-green-500 flex items-center gap-1">
                                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                                Phase 3 Live
                            </span>
                        </div>
                        <label className="cursor-pointer group">
                            <input type="file" className="hidden" onChange={handleUpload} accept=".pdf" />
                            <div className="flex items-center gap-2 bg-white text-black px-5 py-2.5 rounded-full font-bold transition-transform active:scale-95 group-hover:shadow-[0_0_20px_rgba(255,255,255,0.2)]">
                                <Plus className="w-5 h-5" />
                                New Analysis
                            </div>
                        </label>
                    </div>
                </header>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

                    {/* Left Column: History/Docs */}
                    <section className="lg:col-span-3 space-y-4">
                        <h3 className="text-xs font-bold uppercase tracking-wider text-foreground/40 px-2">History</h3>
                        <div className="space-y-2">
                            {history.length === 0 ? (
                                <div className="glass p-4 rounded-2xl text-sm text-foreground/30 text-center italic">
                                    No analyses yet
                                </div>
                            ) : (
                                history.map((doc: any) => (
                                    <button
                                        key={doc.doc_id}
                                        onClick={() => {
                                            setLoading(true);
                                            api.analyzeDocument(doc.doc_id).then(res => {
                                                setReport(res);
                                                setLoading(false);
                                            });
                                        }}
                                        className="w-full text-left glass glass-hover p-4 rounded-2xl group flex items-center justify-between"
                                    >
                                        <div className="flex items-center gap-3 truncate">
                                            <FileText className="w-5 h-5 text-purple/60 group-hover:text-purple shrink-0" />
                                            <div className="truncate">
                                                <p className="text-sm font-bold truncate">{doc.company || doc.filename}</p>
                                                <p className="text-[10px] text-foreground/40">{new Date(doc.uploaded_at).toLocaleDateString()}</p>
                                            </div>
                                        </div>
                                        <ChevronRight className="w-4 h-4 text-foreground/20 group-hover:text-foreground/60 transition-transform group-hover:translate-x-1" />
                                    </button>
                                ))
                            )}
                        </div>
                    </section>

                    {/* Main Dashboard Area */}
                    <section className="lg:col-span-9">
                        <AnimatePresence mode="wait">
                            {loading ? (
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -20 }}
                                    className="h-[60vh] flex flex-col items-center justify-center space-y-6 text-center"
                                >
                                    <div className="relative">
                                        <Loader2 className="w-16 h-16 text-purple animate-spin" />
                                        <Shield className="w-6 h-6 text-white absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                                    </div>
                                    <div className="w-full max-w-xs space-y-4">
                                        <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                            <motion.div
                                                initial={{ width: 0 }}
                                                animate={{ width: `${progress}%` }}
                                                className="h-full bg-purple shadow-[0_0_10px_rgba(139,92,246,0.5)]"
                                            />
                                        </div>
                                        <div className="flex justify-between items-center px-1">
                                            <h2 className="text-sm font-bold">{status || "Processing..."}</h2>
                                            <span className="text-xs font-mono text-purple">{progress}%</span>
                                        </div>
                                        <p className="text-foreground/40 text-[10px] tracking-wider uppercase">
                                            ARIA is fusing multiple data sources
                                        </p>
                                    </div>
                                </motion.div>
                            ) : report ? (
                                <motion.div
                                    initial={{ opacity: 0, scale: 0.98 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    className="space-y-8"
                                >
                                    {/* Top Stats Row */}
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                        <div className="glass p-6 rounded-3xl relative overflow-hidden group">
                                            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                                                <Shield className="w-16 h-16" />
                                            </div>
                                            <h4 className="text-xs font-bold uppercase tracking-widest text-foreground/40 mb-4">Aria Risk Score</h4>
                                            <div className="flex items-end gap-3">
                                                <span className="text-5xl font-black">{report.overall_risk_score}</span>
                                                <span className="text-sm font-bold mb-2 text-foreground/40">/100</span>
                                            </div>
                                            <p className={`text-sm mt-2 font-bold ${report.overall_risk_score > 70 ? 'text-risk-high' :
                                                report.overall_risk_score > 40 ? 'text-risk-medium' : 'text-risk-low'
                                                }`}>
                                                {report.rating}
                                            </p>
                                        </div>

                                        <div className="glass p-6 rounded-3xl flex flex-col justify-between">
                                            <h4 className="text-xs font-bold uppercase tracking-widest text-foreground/40">Entity Analyzed</h4>
                                            <p className="text-2xl font-black mt-2 truncate">{report.company}</p>
                                            <div className="flex items-center gap-2 mt-4 text-[10px] text-foreground/40">
                                                <div className="w-1.5 h-1.5 rounded-full bg-purple" />
                                                Confidence: High
                                            </div>
                                        </div>

                                        <div className="glass p-6 rounded-3xl flex flex-col justify-between group">
                                            <h4 className="text-xs font-bold uppercase tracking-widest text-foreground/40">Final Artifact</h4>
                                            <button
                                                onClick={() => api.downloadReport(report.doc_id)}
                                                className="bg-purple/10 hover:bg-purple/20 text-purple border border-purple/20 py-3 rounded-2xl font-bold flex items-center justify-center gap-2 transition-colors mt-2"
                                            >
                                                <Download className="w-5 h-5" />
                                                Download PDF Report
                                            </button>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                                        {/* Financial Anomalies */}
                                        <div className="space-y-4">
                                            <div className="flex items-center gap-2 px-2">
                                                <TrendingDown className="w-5 h-5 text-purple" />
                                                <h3 className="font-bold">Financial Signals</h3>
                                            </div>
                                            <div className="bg-card p-4 rounded-3xl border border-white/5 space-y-4">
                                                <p className="text-sm text-foreground/60 italic leading-relaxed">
                                                    "{report.financial_signals.summary}"
                                                </p>
                                                <div className="space-y-3">
                                                    {report.financial_signals.anomalies.map((anom: any, idx: number) => (
                                                        <div key={idx} className="p-4 bg-white/5 rounded-2xl flex gap-4 items-start">
                                                            <div className={`p-1.5 rounded-lg shrink-0 mt-0.5 ${anom.severity === 'high' ? 'bg-risk-high/20 text-risk-high' : 'bg-risk-medium/20 text-risk-medium'
                                                                }`}>
                                                                <AlertTriangle className="w-4 h-4" />
                                                            </div>
                                                            <div className="space-y-1">
                                                                <p className="text-sm font-bold">{anom.metric}</p>
                                                                <p className="text-xs text-foreground/50 leading-relaxed">{anom.observation}</p>
                                                            </div>
                                                        </div>
                                                    ))}
                                                    {report.financial_signals.anomalies.length === 0 && (
                                                        <div className="text-center py-4 text-xs text-foreground/30 flex items-center justify-center gap-2">
                                                            <CheckCircle className="w-4 h-4 text-risk-low" />
                                                            No major anomalies detected
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>

                                        {/* News Intelligence */}
                                        <div className="space-y-4">
                                            <div className="flex items-center gap-2 px-2">
                                                <Globe className="w-5 h-5 text-blue-400" />
                                                <h3 className="font-bold">Market Intelligence</h3>
                                            </div>
                                            <div className="bg-card p-4 rounded-3xl border border-white/5 space-y-4">
                                                <p className="text-sm text-foreground/60 italic leading-relaxed">
                                                    "{report.news_signals.summary}"
                                                </p>
                                                <div className="space-y-3">
                                                    {report.news_signals.signals.map((sig: any, idx: number) => (
                                                        <div key={idx} className="p-4 bg-white/5 rounded-2xl flex gap-4 items-start">
                                                            <div className={`p-1.5 rounded-lg shrink-0 mt-0.5 ${sig.impact === 'high' ? 'bg-risk-high/20 text-risk-high' : 'bg-risk-medium/20 text-risk-medium'
                                                                }`}>
                                                                <Globe className="w-4 h-4" />
                                                            </div>
                                                            <div className="space-y-1">
                                                                <p className="text-sm font-bold">{sig.signal}</p>
                                                                <p className="text-xs text-foreground/50 leading-relaxed">{sig.description}</p>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>

                                                {/* News Feed */}
                                                <div className="pt-2">
                                                    <p className="text-[10px] font-black tracking-widest text-foreground/20 uppercase mb-3">Live Sources</p>
                                                    <div className="space-y-2">
                                                        {report.news_signals.top_stories?.map((story: any, idx: number) => (
                                                            <a
                                                                href={story.url}
                                                                target="_blank"
                                                                key={idx}
                                                                className="flex items-center justify-between p-3 bg-white/5 rounded-xl text-[10px] hover:bg-white/10 transition-colors group"
                                                            >
                                                                <span className="font-bold truncate max-w-[70%]">{story.title}</span>
                                                                <span className="text-purple group-hover:underline">{story.source}</span>
                                                            </a>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            ) : (
                                /* Empty / Landing State */
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="h-[60vh] flex flex-col items-center justify-center text-center space-y-8"
                                >
                                    <div className="animate-float">
                                        <div className="relative">
                                            <div className="absolute inset-0 bg-purple blur-3xl opacity-20" />
                                            <div className="relative glass p-8 rounded-[40px] border-white/10">
                                                <Shield className="w-20 h-20 text-purple" />
                                            </div>
                                        </div>
                                    </div>
                                    <div className="space-y-2 max-w-md">
                                        <h2 className="text-3xl font-black">Ready for Deployment</h2>
                                        <p className="text-foreground/40">
                                            Upload a financial PDF (Annual Report, 10-K, etc.) and let ARIA cross-reference the internal data with live global markets.
                                        </p>
                                    </div>
                                    <label className="cursor-pointer">
                                        <input type="file" className="hidden" onChange={handleUpload} accept=".pdf" />
                                        <div className="flex items-center gap-3 bg-white text-black px-8 py-4 rounded-full font-bold text-lg hover:scale-105 transition-transform hover:shadow-2xl hover:shadow-purple/20">
                                            <Upload className="w-6 h-6" />
                                            Start Risk Analysis
                                        </div>
                                    </label>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </section>

                </div>
            </div>
        </main>
    );
}
