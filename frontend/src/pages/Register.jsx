import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import * as authApi from "../api/auth";
import { errorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Register() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await authApi.register(form);
      await login(form.email, form.password);
      navigate("/");
    } catch (err) {
      setError(errorMessage(err, "Could not create the account."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="auth-card">
      <h1>Create account</h1>
      <form onSubmit={submit}>
        <label>Full name
          <input value={form.full_name} onChange={set("full_name")} required maxLength={120} autoFocus />
        </label>
        <label>Email
          <input type="email" value={form.email} onChange={set("email")} required />
        </label>
        <label>Password
          <input type="password" value={form.password} onChange={set("password")} required minLength={8} maxLength={128} />
          <span className="hint">At least 8 characters.</span>
        </label>
        {error && <p className="error" role="alert">{error}</p>}
        <button className="btn btn-primary" disabled={busy}>{busy ? "Creating…" : "Create account"}</button>
      </form>
      <p className="muted">Already registered? <Link to="/login">Log in</Link></p>
    </main>
  );
}
