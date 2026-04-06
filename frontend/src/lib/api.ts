import axios from 'axios';

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
        const res = await fetch(`${API_BASE_URL}/api/analyze/${docId}`);
        return res.json();
    },

    fetchFiling: async (ticker: string) => {
        const res = await fetch(`${API_BASE_URL}/api/fetch-filing/${ticker}`);
        if (!res.ok) throw new Error("Failed to fetch filing");
        return res.json();
    },

    getReportUrl: (docId: string) => `${API_BASE_URL}/api/report/${docId}`,
    downloadReport: (docId: string) => {
        window.open(`${API_BASE_URL}/api/report/${docId}`, '_blank');
    }
};
