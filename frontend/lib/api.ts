import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const analysisApi = {
  analyzeSingle: async (text: string) => {
    const response = await api.post("/analyze", { text });
    return response.data;
  },

  analyzeBulk: async (reviews: string[]) => {
    const response = await api.post("/bulk-analyze", { reviews });
    return response.data;
  },

  uploadCsv: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file, file.name);
    const response = await api.post("/upload-csv", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },

  scrapeAndAnalyze: async (business_name: string, location?: string) => {
    const response = await api.post("/scrape-and-analyze", {
      business_name,
      location,
      max_reviews: 50,
    });
    return response.data;
  },

  getSummary: async (batchId: string) => {
    const response = await api.get(`/summary/${batchId}`);
    return response.data;
  },

  getHistory: async (page = 1, limit = 10) => {
    const response = await api.get("/history", {
      params: { page, limit },
    });
    return response.data;
  },

  getHealth: async () => {
    const response = await api.get("/health");
    return response.data;
  },
};

export default api;
