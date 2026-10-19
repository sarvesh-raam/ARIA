import axios from 'axios';
import type { DocumentSummary, QueryAnswer, RiskReport } from './types';
import { getWorkspaceId } from './workspace';

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Every request carries this browser's workspace ID, so the backend only returns its own reports
const http = axios.create({ baseURL: API_BASE_URL });
http.interceptors.request.use((config) => {
    config.headers.set('X-Workspace-Id', getWorkspaceId());
    return config;
});

// Turn an API failure into a message the user can act on (backend sends { detail })
export const getErrorMessage = (err: unknown): string => {
    if (axios.isAxiosError(err)) {
        if (!err.response) return 'Cannot reach the ARIA backend. Check that it is running and try again.';
        const detail = err.response.data?.detail;
        if (typeof detail === 'string') return detail;
        return `Request failed (${err.response.status}).`;
    }
    return 'Something went wrong. Please try again.';
};

export const isNotFound = (err: unknown) => axios.isAxiosError(err) && err.response?.status === 404;

export const newTaskId = () => 'task_' + Math.random().toString(36).substring(2, 10);

export const api = {
    uploadDocument: async (file: File, taskId?: string): Promise<{ doc_id: string; company?: string; status: string }> => {
        const formData = new FormData();
        formData.append('file', file);
        const response = await http.post('/api/upload', formData, {
            params: taskId ? { task_id: taskId } : undefined,
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },

    // Round-trip time to the backend's health check, in ms (throws if unreachable)
    ping: async () => {
        const start = performance.now();
        await axios.get(`${API_BASE_URL}/`, { timeout: 10000 });
        return Math.round(performance.now() - start);
    },

    listDocuments: async (): Promise<DocumentSummary[]> => {
        const response = await http.get('/api/documents');
        return response.data;
    },

    queryDocument: async (docId: string, question: string): Promise<QueryAnswer> => {
        const response = await http.post('/api/query', { doc_id: docId, question });
        return response.data;
    },

    // Runs a new analysis (LLM + news); progress is reported under taskId
    analyzeDocument: async (docId: string, taskId?: string): Promise<RiskReport> => {
        const response = await http.get(`/api/analyze/${docId}`, { params: taskId ? { task_id: taskId } : undefined });
        return response.data;
    },

    // Last saved analysis, no LLM call; 404 if the document was never analyzed
    getAnalysis: async (docId: string): Promise<RiskReport> => {
        const response = await http.get(`/api/analysis/${docId}`);
        return response.data;
    },

    // A plain link can't send the workspace header, so fetch the PDF and save it from memory
    downloadReport: async (docId: string) => {
        let response;
        try {
            response = await http.get(`/api/report/${docId}`, { responseType: 'blob' });
        } catch (err) {
            // Errors arrive as a Blob too; decode them so getErrorMessage can show the backend's detail
            if (axios.isAxiosError(err) && err.response?.data instanceof Blob) {
                try {
                    err.response.data = JSON.parse(await err.response.data.text());
                } catch { /* not JSON, keep the generic message */ }
            }
            throw err;
        }
        const disposition: string = response.headers['content-disposition'] ?? '';
        const filename = /filename="?([^";]+)"?/.exec(disposition)?.[1] ?? `ARIA_Report_${docId}.pdf`;
        const url = URL.createObjectURL(response.data);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.click();
        // Revoking right away can cancel the download in some browsers
        setTimeout(() => URL.revokeObjectURL(url), 10000);
    },
};
