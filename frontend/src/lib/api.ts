import axios from 'axios';

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

export const api = {
    uploadDocument: async (file: File, taskId?: string) => {
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

    listDocuments: async () => {
        const response = await axios.get(`${API_BASE_URL}/api/documents`);
        return response.data;
    },

    queryDocument: async (docId: string, question: string) => {
        const response = await axios.post(`${API_BASE_URL}/api/query`, {
            doc_id: docId,
            question: question,
        });
        return response.data;
    },

    analyzeDocument: async (docId: string) => {
        const response = await axios.get(`${API_BASE_URL}/api/analyze/${docId}`);
        return response.data;
    },

    getReportUrl: (docId: string) => `${API_BASE_URL}/api/report/${docId}`,
    downloadReport: (docId: string) => {
        window.open(`${API_BASE_URL}/api/report/${docId}`, '_blank');
    }
};
