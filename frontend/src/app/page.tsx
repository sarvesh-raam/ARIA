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
        <div className="flex min-h-screen bg-background text-foreground font-sans overflow-hidden transition-all">
            
            {/* --- SIDE NAVIGATION RAIL --- */}
            <aside className="w-16 md:w-20 lg:w-64 border-r border-white/5 flex flex-col bg-card/30 backdrop-blur-3xl shrink-0 z-50">
                <div className="p-4 lg:p-6 flex items-center gap-3">
                    <div className="p-2 bg-brand rounded-lg shadow-glow-cyan shrink-0 mx-auto lg:mx-0">
                        <Shield className="w-5 h-5 lg:w-6 lg:h-6 text-background" />
                    </div>
                    <span className="hidden lg:block font-display text-lg tracking-tight text-white uppercase">Aria <span className="text-brand">HQ</span></span>
                </div>

                <nav className="flex-1 px-2 lg:px-4 space-y-2 mt-4">
                    <button 
                        onClick={() => setActiveView('dashboard')}
                        className={`nav-item w-full flex justify-center lg:justify-start ${activeView === 'dashboard' ? 'text-brand bg-white/5' : ''}`}
                    >
                        <LayoutDashboard className="w-5 h-5 shrink-0" />
                        <span className="hidden lg:block font-medium">Intelligence</span>
                    </button>
                    <button 
                        onClick={() => setActiveView('history')}
                        className={`nav-item w-full flex justify-center lg:justify-start ${activeView === 'history' ? 'text-brand bg-white/5' : ''}`}
                    >
                        <History className="w-5 h-5 shrink-0" />
                        <span className="hidden lg:block font-medium">Archives</span>
                    </button>
                    <div className="h-px bg-white/5 my-4" />
                    <button 
                        onClick={() => setActiveView('market')}
                        className={`nav-item w-full flex justify-center lg:justify-start ${activeView === 'market' ? 'text-brand bg-white/5' : ''}`}
                    >
                        <Activity className="w-5 h-5 shrink-0" />
                        <span className="hidden lg:block font-medium">Market Pulse</span>
                    </button>
                </nav>

                <div className="p-2 lg:p-4 mt-auto">
                    <div className="glass-card bg-slate-900/40 p-3 hidden lg:block">
                        <div className="flex items-center gap-2 mb-2">
                            <Server className="w-3 h-3 text-brand" />
                            <span className="text-[10px] font-black uppercase text-slate-500">System Mesh</span>
                        </div>
                        <div className="space-y-1.5">
                            <div className="flex justify-between items-center text-[10px]">
                                <span className="text-slate-400">Node</span>
                                <span className="text-brand font-bold">READY</span>
                            </div>
                        </div>
                    </div>
                    <button className="nav-item w-full mt-4 text-slate-500 hover:text-red-400 flex justify-center lg:justify-start">
                        <LogOut className="w-5 h-5 shrink-0" />
                        <span className="hidden lg:block font-medium">Logout</span>
                    </button>
                </div>
            </aside>

            {/* --- MAIN CONTENT AREA --- */}
            <main className="flex-1 flex flex-col relative overflow-hidden">
                <div className="animate-scan absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-brand to-transparent z-50 pointer-events-none" />
                
                {/* Dashboard Header */}
                <header className="h-16 lg:h-20 border-b border-white/5 px-4 lg:px-8 flex items-center justify-between bg-background/50 backdrop-blur-md sticky top-0 z-40">
                    <div className="flex flex-col">
                        <span className="text-[8px] lg:text-[10px] font-black tracking-widest text-slate-500 uppercase">Audit Workspace</span>
                        <h2 className="text-sm lg:text-xl font-display font-semibold text-white truncate max-w-[150px] sm:max-w-none">
                            {report ? report.company : activeView === 'history' ? 'Archives' : 'Strategic Overview'}
                        </h2>
                    </div>

                    <div className="flex items-center gap-2 lg:gap-4">
                        <div className="hidden sm:flex items-center gap-6 px-4 py-2 bg-slate-900/50 rounded-lg border border-white/5 mr-4">
                            <div className="flex flex-col items-center">
                                <span className="text-[9px] text-slate-500 uppercase font-black mb-0.5">Latency</span>
                                <span className="text-xs font-bold text-brand">240ms</span>
                            </div>
                        </div>

                        <label className="btn-primary flex items-center gap-2 cursor-pointer py-2 px-3 lg:px-4 text-xs lg:text-sm">
                            <input type="file" className="hidden" onChange={handleUpload} accept=".pdf" />
                            <Upload className="w-3 h-3 lg:w-4 lg:h-4" />
                            <span className="hidden sm:block">Deploy Audit</span>
                            <span className="sm:hidden">Upload</span>
                        </label>
                    </div>
                </header>

                {/* Dashboard Content */}
                <div className="flex-1 overflow-y-auto p-4 lg:p-8 relative">
                    <AnimatePresence mode="wait">
                        {loading ? (
                            <motion.div 
                                key="loading"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="h-[70vh] flex flex-col items-center justify-center space-y-6 lg:space-y-8"
                            >
                                <div className="p-6 lg:p-8 border-2 border-brand/20 rounded-[30px] lg:rounded-[40px] relative">
                                    <Loader2 className="w-12 h-12 lg:w-20 lg:h-20 text-brand animate-spin" />
                                </div>
                                <div className="text-center space-y-4 max-w-[280px] lg:max-w-sm">
                                    <h3 className="text-lg lg:text-2xl font-display text-white">{status}</h3>
                                    <div className="h-1 w-full bg-slate-900 rounded-full overflow-hidden">
                                        <motion.div className="h-full bg-brand" initial={{ width: 0 }} animate={{ width: `${progress}%` }} />
                                    </div>
                                </div>
                            </motion.div>
                        ) : report && activeView === 'dashboard' ? (
                            <motion.div key="report" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6 lg:space-y-8">
                                <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 lg:gap-6">
                                    <div className="lg:col-span-3 glass-card bg-slate-900/40 p-4 lg:p-6 flex flex-col lg:flex-row items-center gap-6 border-l-4 border-l-brand">
                                        <div className="shrink-0 text-center lg:text-left">
                                            <span className="text-[10px] font-black text-slate-500 uppercase">Risk Index</span>
                                            <div className="flex items-end gap-1 justify-center lg:justify-start">
                                                <h2 className="text-5xl lg:text-7xl font-black text-white">{report.overall_risk_score}</h2>
                                                <span className="text-lg font-bold text-slate-600 mb-2">/100</span>
                                            </div>
                                        </div>
                                        <div className="flex-1 text-center lg:text-left">
                                            <h4 className="font-display text-xl lg:text-2xl text-slate-200 mb-2">Narrative</h4>
                                            <p className="text-slate-400 text-xs lg:text-sm leading-relaxed mb-4">
                                                Risk profile determined as **{report.rating}** based on forensic audit fusion.
                                            </p>
                                            <button onClick={() => api.downloadReport(report.doc_id)} className="btn-primary w-full lg:w-auto text-[10px] font-bold">
                                                DOWNLOAD PDF
                                            </button>
                                        </div>
                                    </div>
                                </div>
                                {/* Pillars Grid */}
                                <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 pb-20">
                                    <div className="space-y-4">
                                        <h3 className="font-display text-lg text-white flex items-center gap-2">
                                            <FileText className="w-4 h-4 text-brand" /> Internal Signals
                                        </h3>
                                        <div className="grid gap-4">
                                            {report.financial_signals.anomalies.map((anom: any, i: number) => (
                                                <div key={i} className="glass-card p-4 border-l-2 border-brand">
                                                    <h5 className="text-[10px] font-black text-brand uppercase mb-1">{anom.metric}</h5>
                                                    <p className="text-xs text-white leading-relaxed">{anom.observation}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </motion.div>
                        ) : activeView === 'market' ? (
                            <div className="h-[60vh] flex flex-col items-center justify-center text-center p-6 space-y-4">
                                <Globe className="w-12 h-12 text-brand opacity-20" />
                                <p className="text-slate-500 text-sm">Real-time market stream active.</p>
                            </div>
                        ) : activeView === 'history' ? (
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                {history.map((doc: any) => (
                                    <button key={doc.doc_id} className="glass-card p-4 text-left hover:border-brand transition-all">
                                        <h5 className="text-white font-bold truncate">{doc.filename}</h5>
                                        <p className="text-[10px] text-slate-500 uppercase">{new Date(doc.uploaded_at).toLocaleDateString()}</p>
                                    </button>
                                ))}
                            </div>
                        ) : (
                            <motion.div 
                                key="empty"
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                                className="h-[75vh] flex flex-col items-center justify-center text-center px-4"
                            >
                                <div className="relative mb-8 lg:mb-12">
                                    <div className="absolute inset-0 bg-brand/30 blur-[60px] lg:blur-[100px] animate-pulse rounded-full" />
                                    <div className="relative glass-card bg-slate-950 p-8 lg:p-16 rounded-[40px] lg:rounded-[60px] border-white/5 border shadow-2xl">
                                        <Shield className="w-16 h-16 lg:w-32 lg:h-32 text-brand mx-auto" />
                                    </div>
                                </div>
                                <div className="space-y-4 lg:space-y-6 max-w-xl">
                                    <h2 className="text-3xl lg:text-5xl font-display font-bold text-white tracking-tight">System Initialization</h2>
                                    <p className="text-slate-400 text-sm lg:text-lg leading-relaxed">
                                        Deploy ARIA to perform autonomous, forensic financial audits combined with real-time semantic market cross-referencing.
                                    </p>
                                    
                                    <div className="flex flex-col sm:flex-row items-center justify-center gap-4 lg:gap-8 pt-4">
                                        <label className="btn-primary w-full sm:w-auto cursor-pointer flex items-center justify-center gap-3 active:scale-95 transition-transform py-4 px-8">
                                            <input type="file" className="hidden" onChange={handleUpload} accept=".pdf" />
                                            <Upload className="w-5 h-5" />
                                            <span className="font-bold">Initialize Audit Engine</span>
                                        </label>
                                        <button onClick={() => setActiveView('history')} className="text-slate-500 font-bold text-xs lg:text-sm hover:text-white flex items-center gap-2">
                                            <History className="w-4 h-4" /> VIEW ARCHIVES
                                        </button>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* --- CORPORATE FOOTER --- */}
                <footer className="h-8 lg:h-10 border-t border-white/5 px-4 lg:px-8 flex items-center justify-between text-[7px] lg:text-[9px] font-black text-slate-600 uppercase tracking-widest bg-slate-950">
                    <div className="flex items-center gap-2 lg:gap-4">
                        <span className="hidden sm:inline">Cluster: 0xARIA-MAINNET</span>
                        <div className="w-1 h-1 rounded-full bg-brand" />
                        <span>v4.2.0-PRO</span>
                    </div>
                    <span>(C) 2026 ARIA COORPORATE</span>
                </footer>
            </main>
        </div>
    );
}
