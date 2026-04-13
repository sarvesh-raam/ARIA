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
    Search,
    History,
    Activity,
    Server,
    LayoutDashboard,
    LogOut,
    ChevronRight,
    CircleDashed,
    BarChart3,
    ArrowUpRight
} from 'lucide-react';
import { api, API_BASE_URL } from '@/lib/api';

export default function CorporateDashboard() {
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState("");
    const [progress, setProgress] = useState(0);
    const [report, setReport] = useState<any>(null);
    const [history, setHistory] = useState<any[]>([]);
    const [activeView, setActiveView] = useState<'dashboard' | 'history' | 'market'>('dashboard');

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
            setStatus("Initializing Neural Audit...");
            const tempTaskId = "task_" + Math.random().toString(36).substring(7);

            const eventSource = new EventSource(`${API_BASE_URL}/api/progress/${tempTaskId}`);
            eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                setProgress(data.percentage);
                setStatus(data.status);
            };

            const uploadRes = await api.uploadDocument(selected, tempTaskId);
            const docId = uploadRes.doc_id;

            eventSource.close();
            const analysisSource = new EventSource(`${API_BASE_URL}/api/progress/${docId}`);
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
        } finally {
            setLoading(false);
            setStatus("");
        }
    };

    return (
        <div className="flex min-h-screen bg-background text-foreground font-sans overflow-hidden">
            
            {/* --- SIDE NAVIGATION RAIL --- */}
            <aside className="w-20 lg:w-64 border-r border-white/5 flex flex-col bg-card/30 backdrop-blur-3xl shrink-0">
                <div className="p-6 flex items-center gap-3">
                    <div className="p-2 bg-brand rounded-lg shadow-glow-cyan shrink-0">
                        <Shield className="w-6 h-6 text-background" />
                    </div>
                    <span className="hidden lg:block font-display text-xl tracking-tight text-white uppercase">Aria <span className="text-brand">HQ</span></span>
                </div>

                <nav className="flex-1 px-4 space-y-2 mt-4">
                    <button 
                        onClick={() => setActiveView('dashboard')}
                        className={`nav-item w-full ${activeView === 'dashboard' ? 'text-brand bg-white/5' : ''}`}
                    >
                        <LayoutDashboard className="w-5 h-5 shrink-0" />
                        <span className="hidden lg:block font-medium">Intelligence</span>
                    </button>
                    <button 
                        onClick={() => setActiveView('history')}
                        className={`nav-item w-full ${activeView === 'history' ? 'text-brand bg-white/5' : ''}`}
                    >
                        <History className="w-5 h-5 shrink-0" />
                        <span className="hidden lg:block font-medium">Audit History</span>
                    </button>
                    <div className="h-px bg-white/5 my-4" />
                    <button 
                        onClick={() => setActiveView('market')}
                        className={`nav-item w-full ${activeView === 'market' ? 'text-brand bg-white/5' : ''}`}
                    >
                        <Activity className="w-5 h-5 shrink-0" />
                        <span className="hidden lg:block font-medium">Market Pulse</span>
                    </button>
                </nav>

                <div className="p-4 mt-auto">
                    <div className="glass-card bg-slate-900/40 p-3 hidden lg:block">
                        <div className="flex items-center gap-2 mb-2">
                            <Server className="w-3 h-3 text-brand" />
                            <span className="text-[10px] font-black uppercase text-slate-500">System Mesh</span>
                        </div>
                        <div className="space-y-1.5">
                            <div className="flex justify-between items-center text-[10px]">
                                <span className="text-slate-400">Node Cluster</span>
                                <span className="text-brand font-bold">ACTIVE</span>
                            </div>
                            <div className="flex justify-between items-center text-[10px]">
                                <span className="text-slate-400">LLM Instance</span>
                                <span className="text-brand font-bold">READY</span>
                            </div>
                        </div>
                    </div>
                    <button className="nav-item w-full mt-4 text-slate-500 hover:text-red-400">
                        <LogOut className="w-5 h-5 shrink-0" />
                        <span className="hidden lg:block font-medium">Shutdown</span>
                    </button>
                </div>
            </aside>

            {/* --- MAIN CONTENT AREA --- */}
            <main className="flex-1 flex flex-col relative overflow-hidden">
                <div className="animate-scan absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-brand to-transparent z-50 pointer-events-none" />
                
                {/* Dashboard Header */}
                <header className="h-20 border-b border-white/5 px-8 flex items-center justify-between bg-background/50 backdrop-blur-md sticky top-0 z-40">
                    <div className="flex flex-col">
                        <span className="text-[10px] font-black tracking-widest text-slate-500 uppercase">Audit Workspace</span>
                        <h2 className="text-xl font-display font-semibold text-white">
                            {report ? `Analysis: ${report.company}` : activeView === 'history' ? 'System Audit Archives' : 'Strategic Overview'}
                        </h2>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="hidden lg:flex items-center gap-6 px-4 py-2 bg-slate-900/50 rounded-lg border border-white/5 mr-4">
                            <div className="flex flex-col items-center">
                                <span className="text-[9px] text-slate-500 uppercase font-black mb-0.5">Coverage</span>
                                <span className="text-xs font-bold text-slate-200">GLOBAL</span>
                            </div>
                            <div className="w-px h-6 bg-white/10" />
                            <div className="flex flex-col items-center">
                                <span className="text-[9px] text-slate-500 uppercase font-black mb-0.5">Latency</span>
                                <span className="text-xs font-bold text-brand">240ms</span>
                            </div>
                        </div>

                        <label className="btn-primary flex items-center gap-2 cursor-pointer">
                            <input type="file" className="hidden" onChange={handleUpload} accept=".pdf" />
                            <Upload className="w-4 h-4" />
                            <span className="hidden sm:block">Deploy New Audit</span>
                        </label>
                    </div>
                </header>

                {/* Dashboard Content */}
                <div className="flex-1 overflow-y-auto p-8 relative">
                    <AnimatePresence mode="wait">
                        {loading ? (
                            <motion.div 
                                key="loading"
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.95 }}
                                className="h-[70vh] flex flex-col items-center justify-center space-y-8"
                            >
                                <div className="p-8 border-2 border-brand/20 rounded-[40px] relative">
                                    <div className="absolute inset-0 border border-brand/40 rounded-[40px] animate-pulse" />
                                    <Loader2 className="w-20 h-20 text-brand animate-spin" />
                                </div>
                                <div className="text-center space-y-4 max-w-sm">
                                    <h3 className="text-2xl font-display text-white">{status}</h3>
                                    <div className="space-y-2">
                                        <div className="h-1 w-full bg-slate-900 rounded-full overflow-hidden">
                                            <motion.div 
                                                className="h-full bg-brand"
                                                initial={{ width: 0 }}
                                                animate={{ width: `${progress}%` }}
                                            />
                                        </div>
                                        <div className="flex justify-between text-[10px] font-black text-slate-500 uppercase tracking-widest">
                                            <span>Fusion Engine Phase</span>
                                            <span className="text-brand">{progress}% COMPLETE</span>
                                        </div>
                                    </div>
                                    <p className="text-slate-500 text-xs italic">ARIA is analyzing multi-source structural datasets...</p>
                                </div>
                            </motion.div>
                        ) : report && activeView === 'dashboard' ? (
                            <motion.div 
                                key="report"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="space-y-8"
                            >
                                {/* Executive Summary Bar */}
                                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                                    <div className="lg:col-span-3 glass-card bg-slate-900/40 flex flex-col md:flex-row items-center gap-8 border-l-4 border-l-brand">
                                        <div className="shrink-0 space-y-2 text-center md:text-left">
                                            <span className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">Risk Exposure Index</span>
                                            <div className="flex items-end gap-2 justify-center md:justify-start">
                                                <h2 className="text-7xl font-sans font-black text-white">{report.overall_risk_score}</h2>
                                                <span className="text-xl font-bold text-slate-600 mb-2">/100</span>
                                            </div>
                                            <div className={`risk-badge inline-block ${
                                                report.overall_risk_score > 70 ? 'text-risk-critical' : 
                                                report.overall_risk_score > 40 ? 'text-risk-elevated' : 'text-risk-stable'
                                            }`}>
                                                {report.rating}
                                            </div>
                                        </div>
                                        <div className="flex-1 space-y-4">
                                            <h4 className="font-display text-2xl text-slate-200">Institutional Audit Narrative</h4>
                                            <p className="text-slate-400 text-sm leading-relaxed max-w-2xl">
                                                Based on structural forensic analysis of internal filings and external market intelligence, 
                                                ARIA has determined a **{report.rating}** posture for **{report.company}**. 
                                                {report.financial_signals.summary}
                                            </p>
                                            <div className="flex gap-4">
                                                <button 
                                                    onClick={() => api.downloadReport(report.doc_id)}
                                                    className="flex items-center gap-2 text-[11px] font-bold text-brand hover:underline"
                                                >
                                                    <Download className="w-3.5 h-3.5" />
                                                    GENERATE EXECUTIVE PDF
                                                </button>
                                                <div className="w-px h-4 bg-white/10" />
                                                <div className="flex items-center gap-1.5 text-[11px] font-bold text-slate-500">
                                                    <CheckCircle className="w-3.5 h-3.5 text-brand" />
                                                    VERIFIED AUDIT
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="glass-card flex flex-col justify-center items-center text-center space-y-4 relative overflow-hidden group">
                                        <div className="absolute top-0 right-0 p-2 opacity-5 scale-150 rotate-12 group-hover:scale-[1.6] transition-transform">
                                            <Shield className="w-32 h-32" />
                                        </div>
                                        <BarChart3 className="w-10 h-10 text-brand" />
                                        <div className="space-y-1">
                                            <h4 className="text-xl font-display text-white">Internal Pulse</h4>
                                            <p className="text-xs text-slate-500 uppercase tracking-widest font-black">Anomaly Detector</p>
                                        </div>
                                        <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                            <div className="h-full bg-brand w-2/3" />
                                        </div>
                                        <span className="text-[10px] text-slate-400">Confidence Threshold: 92%</span>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
                                    {/* Financial Pillar */}
                                    <div className="space-y-6">
                                        <div className="flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400">
                                                <FileText className="w-4 h-4" />
                                            </div>
                                            <h3 className="font-display text-xl text-white">Forensic Financial Signals</h3>
                                        </div>

                                        <div className="space-y-4">
                                            {report.financial_signals.anomalies.length > 0 ? report.financial_signals.anomalies.map((anom: any, idx: number) => (
                                                <div key={idx} className="glass-card hover:bg-slate-900/60 flex gap-6">
                                                    <div className={`w-1 shrink-0 rounded-full ${
                                                        anom.severity === 'high' ? 'bg-risk-critical' : 'bg-risk-elevated'
                                                    }`} />
                                                    <div className="space-y-2">
                                                        <div className="flex items-center justify-between">
                                                            <h5 className="font-bold text-white uppercase text-xs tracking-wider">{anom.metric}</h5>
                                                            <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded ${
                                                                anom.severity === 'high' ? 'bg-risk-critical/10 text-risk-critical' : 'bg-risk-elevated/10 text-risk-elevated'
                                                            }`}>{anom.severity} Impact</span>
                                                        </div>
                                                        <p className="text-sm text-slate-400 leading-relaxed">{anom.observation}</p>
                                                    </div>
                                                </div>
                                            )) : (
                                                <div className="glass-card text-center py-12 border-dashed">
                                                    <CheckCircle className="w-12 h-12 text-risk-stable mx-auto mb-4 opacity-40" />
                                                    <p className="text-slate-500 text-sm">No internal structural anomalies identified.</p>
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {/* Market Pillar */}
                                    <div className="space-y-6">
                                        <div className="flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center text-brand">
                                                <Globe className="w-4 h-4" />
                                            </div>
                                            <h3 className="font-display text-xl text-white">External Market Fusion</h3>
                                        </div>

                                        <div className="space-y-4">
                                            {report.news_signals.signals.map((sig: any, idx: number) => (
                                                <div key={idx} className="glass-card hover:bg-slate-900/60 flex gap-6">
                                                    <div className={`w-1 shrink-0 rounded-full ${
                                                        sig.impact === 'high' ? 'bg-risk-critical' : 'bg-risk-elevated'
                                                    }`} />
                                                    <div className="space-y-2">
                                                        <div className="flex items-center justify-between">
                                                            <h5 className="font-bold text-white uppercase text-xs tracking-wider">{sig.signal}</h5>
                                                            <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded ${
                                                                sig.impact === 'high' ? 'bg-risk-critical/10 text-risk-critical' : 'bg-risk-elevated/10 text-risk-elevated'
                                                            }`}>{sig.impact} Impact</span>
                                                        </div>
                                                        <p className="text-sm text-slate-400 leading-relaxed">{sig.description}</p>
                                                    </div>
                                                </div>
                                            ))}
                                            
                                            {/* Top Stories Small Grid */}
                                            <div className="pt-4 space-y-3">
                                                <span className="text-[10px] font-black text-slate-600 uppercase tracking-widest pl-2">Reference Intelligence Sources</span>
                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                                    {report.news_signals.top_stories?.slice(0, 4).map((story: any, i: number) => (
                                                        <a 
                                                            href={story.url} 
                                                            target="_blank" 
                                                            key={i} 
                                                            className="p-3 bg-white/5 rounded-lg border border-white/5 hover:border-brand/40 transition-all flex items-start justify-between group"
                                                        >
                                                            <div className="space-y-1 max-w-[80%]">
                                                                <p className="text-[10px] text-slate-400 font-bold uppercase truncate">{story.source}</p>
                                                                <p className="text-[11px] text-white font-medium line-clamp-2 group-hover:text-brand transition-colors">{story.title}</p>
                                                            </div>
                                                            <ArrowUpRight className="w-3 h-3 text-slate-600 group-hover:text-brand" />
                                                        </a>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </motion.div>
                        ) : activeView === 'market' ? (
                            <motion.div 
                                key="market"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="space-y-8"
                            >
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                                    <div className="glass-card bg-slate-900/40 p-6 space-y-4">
                                        <div className="flex justify-between items-start">
                                            <Globe className="w-6 h-6 text-brand" />
                                            <span className="text-[10px] font-black text-brand uppercase tracking-widest">Global Scan</span>
                                        </div>
                                        <div className="space-y-1">
                                            <p className="text-2xl font-display text-white">ACTIVE</p>
                                            <p className="text-[10px] text-slate-500 uppercase font-black tracking-widest">Market Monitoring</p>
                                        </div>
                                    </div>
                                    <div className="glass-card bg-slate-900/40 p-6 space-y-4">
                                        <div className="flex justify-between items-start">
                                            <Activity className="w-6 h-6 text-indigo-400" />
                                            <span className="text-[10px] font-black text-indigo-400 uppercase tracking-widest">Volatility</span>
                                        </div>
                                        <div className="space-y-1">
                                            <p className="text-2xl font-display text-white">LOW</p>
                                            <p className="text-[10px] text-slate-500 uppercase font-black tracking-widest">Market Stability</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="glass-card bg-slate-900/60 p-12 text-center space-y-4 border-dashed border-white/10">
                                    <Globe className="w-16 h-16 text-brand/20 mx-auto" />
                                    <h3 className="text-xl font-display text-white">Autonomous Market Intelligence Feed</h3>
                                    <p className="text-slate-500 text-sm max-w-lg mx-auto">
                                        ARIA continues to monitor global financial news and forensic signals. 
                                        Detailed market trends will materialize as more institutional data is ingested into the local vector mesh.
                                    </p>
                                </div>
                            </motion.div>
                        ) : activeView === 'history' ? (
                            <motion.div 
                                key="history"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="space-y-6"
                            >
                                <div className="flex items-center justify-between bg-slate-900/40 p-6 rounded-2xl border border-white/5">
                                    <div className="flex items-center gap-6">
                                        <div className="text-center">
                                            <p className="text-[10px] font-black text-slate-500 uppercase">Analyses</p>
                                            <p className="text-2xl font-display text-white">{history.length}</p>
                                        </div>
                                        <div className="w-px h-10 bg-white/10" />
                                        <div className="text-center">
                                            <p className="text-[10px] font-black text-slate-500 uppercase">Avg Latency</p>
                                            <p className="text-2xl font-display text-brand">1.2s</p>
                                        </div>
                                    </div>
                                    <div className="relative w-72">
                                        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                                        <input 
                                            placeholder="Search archives..." 
                                            className="w-full bg-black/40 border border-white/10 rounded-lg py-2 pl-10 pr-4 text-xs focus:border-brand focus:outline-none transition-all"
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                    {history.map((doc: any) => (
                                        <motion.button
                                            whileHover={{ y: -4 }}
                                            key={doc.doc_id}
                                            onClick={() => {
                                                setLoading(true);
                                                setActiveView('dashboard');
                                                api.analyzeDocument(doc.doc_id).then(res => {
                                                    setReport(res);
                                                    setLoading(false);
                                                });
                                            }}
                                            className="glass-card hover:bg-slate-900/80 text-left space-y-4"
                                        >
                                            <div className="flex justify-between items-start">
                                                <div className="p-2 bg-white/5 rounded-lg">
                                                    <FileText className="w-5 h-5 text-brand" />
                                                </div>
                                                <span className="text-[10px] text-slate-500 font-mono tracking-tighter">ID: {doc.doc_id.slice(0,8)}</span>
                                            </div>
                                            <div className="space-y-1">
                                                <h5 className="text-lg font-display text-white truncate">{doc.company || doc.filename}</h5>
                                                <p className="text-xs text-slate-500 uppercase tracking-widest font-black">{new Date(doc.uploaded_at).toLocaleDateString()}</p>
                                            </div>
                                            <div className="pt-2 flex items-center justify-between">
                                                <span className="text-[10px] text-brand font-bold uppercase tracking-widest flex items-center gap-1.5">
                                                    <CircleDashed className="w-3 h-3 animate-spin" />
                                                    Re-Sync
                                                </span>
                                                <ChevronRight className="w-4 h-4 text-slate-700" />
                                            </div>
                                        </motion.button>
                                    ))}
                                </div>
                            </motion.div>
                        ) : (
                            /* Landing Empty State */
                            <motion.div 
                                key="empty"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="h-[70vh] flex flex-col items-center justify-center text-center space-y-12"
                            >
                                <div className="relative">
                                    <div className="absolute inset-0 bg-brand/30 blur-[100px] animate-pulse" />
                                    <div className="relative glass-card bg-slate-950 p-12 lg:p-16 rounded-[60px] border-white/5 border shadow-2xl">
                                        <Shield className="w-24 h-24 lg:w-32 lg:h-32 text-brand" />
                                    </div>
                                </div>
                                <div className="space-y-4 max-w-xl">
                                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand/10 border border-brand/20 text-brand text-[10px] font-black uppercase tracking-widest mb-2">
                                        Deployment Ready: Phase 4
                                    </div>
                                    <h2 className="text-5xl font-display font-bold text-white tracking-tight">System Initialization</h2>
                                    <p className="text-slate-400 text-lg leading-relaxed">
                                        Deploy ARIA to perform autonomous, forensic financial audits combined with real-time semantic market cross-referencing.
                                    </p>
                                </div>

                                <div className="flex flex-col sm:flex-row items-center justify-center gap-10">
                                    <label className="btn-primary cursor-pointer scale-125 !px-10 !py-4 flex items-center gap-3 active:scale-110">
                                        <input type="file" className="hidden" onChange={handleUpload} accept=".pdf" />
                                        <Upload className="w-5 h-5" />
                                        <span>Initialize Audit Engine</span>
                                    </label>
                                    <button 
                                        onClick={() => setActiveView('history')}
                                        className="text-slate-500 font-bold text-sm flex items-center gap-2 hover:text-white transition-colors"
                                    >
                                        <History className="w-4 h-4" />
                                        VIEW ARCHIVES
                                    </button>
                                </div>


                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* --- CORPORATE FOOTER --- */}
                <footer className="h-10 border-t border-white/5 px-8 flex items-center justify-between text-[9px] font-black text-slate-600 uppercase tracking-widest bg-slate-950">
                    <div className="flex items-center gap-4">
                        <span>Cluster: 0xARIA-MAINNET</span>
                        <div className="w-1 h-1 rounded-full bg-brand" />
                        <span>Build: v4.2.0-PRO-FINAL</span>
                    </div>
                    <div className="flex items-center gap-4">
                        <span className="text-brand">Confidential Strategic Artifact</span>
                        <div className="w-1 h-1 rounded-full bg-slate-800" />
                        <span>(C) 2026 ARIA COORPORATE</span>
                    </div>
                </footer>
            </main>
        </div>
    );
}
