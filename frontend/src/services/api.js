import axios from "axios";

// In production (Vercel), set VITE_API_URL to your Render backend URL
// e.g. https://testsmellrank-backend.onrender.com/api
// In development, the Vite proxy rewrites /api → http://localhost:8000
const API_URL = import.meta.env.VITE_API_URL || "/api";

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

export const authAPI = {
  register: async (userData) => {
    const response = await api.post("/auth/register", userData);
    return response.data;
  },

  login: async (credentials) => {
    const response = await api.post("/auth/login", credentials);
    if (response.data.access_token) {
      localStorage.setItem("token", response.data.access_token);
    }
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get("/auth/me");
    return response.data;
  },

  logout: () => {
    localStorage.removeItem("token");
  },
};

export const uploadGithubRepo = async (repoUrl) => {
  const response = await api.post("/upload/github", { repo_url: repoUrl });
  return response.data;
};

export const uploadZipFile = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post("/upload/zip", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

// ── Project management ──────────────────────────────────────────
export const createProject = async (name, repoUrl) => {
  const response = await api.post("/projects/", { name, repo_url: repoUrl });
  return response.data;
};

export const listProjects = async () => {
  const response = await api.get("/projects/");
  return response.data;
};

export const deleteProject = async (projectId) => {
  const response = await api.delete(`/projects/${projectId}`);
  return response.data;
};

// ── Run management ───────────────────────────────────────────────
export const triggerRun = async (projectId) => {
  const response = await api.post(`/projects/${projectId}/runs`);
  return response.data;
};

export const listRuns = async (projectId) => {
  const response = await api.get(`/projects/${projectId}/runs`);
  return response.data;
};

export const deleteRun = async (projectId, runId) => {
  const response = await api.delete(`/projects/${projectId}/runs/${runId}`);
  return response.data;
};

export const getRun = async (projectId, runId) => {
  const response = await api.get(`/projects/${projectId}/runs/${runId}`);
  return response.data;
};

export const compareRuns = async (projectId, run1Id, run2Id) => {
  const response = await api.get(`/projects/${projectId}/compare`, {
    params: { run1: run1Id, run2: run2Id },
  });
  return response.data;
};

// ── Projects API ────────────────────────────────────────────────────
export const projectsAPI = {
  list: async () => {
    const response = await api.get("/projects/");
    return response.data;
  },

  create: async (name, repoUrl) => {
    const response = await api.post("/projects/", { name, repo_url: repoUrl });
    return response.data;
  },

  delete: async (projectId) => {
    const response = await api.delete(`/projects/${projectId}`);
    return response.data;
  },

  // Runs
  triggerRun: async (projectId) => {
    const response = await api.post(`/projects/${projectId}/runs`);
    return response.data;
  },

  listRuns: async (projectId) => {
    const response = await api.get(`/projects/${projectId}/runs`);
    return response.data;
  },

  getRun: async (projectId, runId) => {
    const response = await api.get(`/projects/${projectId}/runs/${runId}`);
    return response.data;
  },

  deleteRun: async (projectId, runId) => {
    const response = await api.delete(`/projects/${projectId}/runs/${runId}`);
    return response.data;
  },

  compare: async (projectId, run1Id, run2Id) => {
    const response = await api.get(
      `/projects/${projectId}/compare?run1=${run1Id}&run2=${run2Id}`,
    );
    return response.data;
  },

  // Survey
  startSurvey: async (projectId, runId) => {
    const response = await api.post(
      `/projects/${projectId}/runs/${runId}/survey/start`,
    );
    return response.data;
  },

  getSurveyStatus: async (projectId, runId) => {
    const response = await api.get(
      `/projects/${projectId}/runs/${runId}/survey`,
    );
    return response.data;
  },
};

export default api;
