import client from "./client";

export const register = (data) => client.post("/auth/register", data).then((r) => r.data);

export const login = (email, password) => {
    // The backend uses the OAuth2 password flow, which expects form-encoded fields.
    const form = new URLSearchParams({ username: email, password });
    return client.post("/auth/login", form).then((r) => r.data);
};

export const fetchMe = () => client.get("/auth/me").then((r) => r.data);
