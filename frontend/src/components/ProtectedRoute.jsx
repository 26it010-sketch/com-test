import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

// UX only: the real access control is enforced by the API on every request.
export default function ProtectedRoute({ children, adminOnly = false }) {
  const { user, loading } = useAuth();
  if (loading) return <p className="status">Loading…</p>;
  if (!user) return <Navigate to="/login" replace />;
  if (adminOnly && user.role !== "admin") return <Navigate to="/" replace />;
  return children;
}
