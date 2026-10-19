import axios from 'axios';
import type { DocumentSummary, QueryAnswer, RiskReport } from './types';

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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

export const api = {
    uploadDocument: async (file: File, taskId?: string): Promise<{ doc_id: string; company?: string; status: string }> => {
        const formData = new FormData();
        formData.append('file', file);
        const url = taskId ? `${API_BASE_URL}/api/upload?task_id=${taskId}` : `${API_BASE_URL}/api/upload`;
        const response = await axios.post(url, formData, {
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
        const response = await axios.get(`${API_BASE_URL}/api/documents`);
        return response.data;
    },

    queryDocument: async (docId: string, question: string): Promise<QueryAnswer> => {
        const response = await axios.post(`${API_BASE_URL}/api/query`, {
            doc_id: docId,
            question: question,
        });
        return response.data;
    },

    // Runs a new analysis (LLM + news)
    analyzeDocument: async (docId: string): Promise<RiskReport> => {
        const response = await axios.get(`${API_BASE_URL}/api/analyze/${docId}`);
        return response.data;
    },

    // Last saved analysis, no LLM call; 404 if the document was never analyzed
    getAnalysis: async (docId: string): Promise<RiskReport> => {
        const response = await axios.get(`${API_BASE_URL}/api/analysis/${docId}`);
        return response.data;
    },

    reportUrl: (docId: string) => `${API_BASE_URL}/api/report/${docId}`,
};
