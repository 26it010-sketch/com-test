import axios from "axios";

const TOKEN_KEY = "dm_token";

export const tokenStore = {
    get: () => localStorage.getItem(TOKEN_KEY),
    set: (t) => localStorage.setItem(TOKEN_KEY, t),
    clear: () => localStorage.removeItem(TOKEN_KEY),
};

const client = axios.create({
    baseURL: import.meta.env.VITE_API_URL || "/api",
});

client.interceptors.request.use((config) => {
    const token = tokenStore.get();
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

// A 401 means the token is missing/expired/invalid.
// Clear the token and let the app redirect to login.
client.interceptors.response.use(
    (res) => res,
    (err) => {
        const isLoginCall = err.config?.url?.includes("/auth/login");
        if (err.response?.status === 401 && !isLoginCall) {
            tokenStore.clear();
            window.dispatchEvent(new Event("auth:logout"));
        }
        return Promise.reject(err);
    }
);

export function errorMessage(err, fallback = "Something went wrong. Try again.") {
    const detail = err?.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail[0]?.msg) {
        return detail[0].msg.replace(/^Value error, /, "");
    }
    return fallback;
}

export default client;