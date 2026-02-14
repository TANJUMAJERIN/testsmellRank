import axios from "axios";

const API_URL = "/api";

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

export const listUserProjects = async () => {
  const response = await api.get("/upload/projects");
  return response.data;
};

export const detectTestSmells = async (projectPath) => {
  const response = await api.post("/upload/detect-smells", {
    project_path: projectPath,
  });
  return response.data;
};

export default api;
