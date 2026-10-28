
import axios from "axios";
//  "https://python-project-rxyp.onrender.com/api/v1",
    // "http://127.0.0.1:8000/api/v1",

const api = axios.create({
  baseURL:
    import.meta.env.VITE_API_URL ||"https://python-project-rxyp.onrender.com/api/v1",

  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

// Attach Bearer token to every request
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("Token");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

export default api;
