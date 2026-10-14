import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, isAdmin, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="navbar">
      <span className="brand">Document Manager</span>
      {user && (
        <>
          <nav>
            <NavLink to="/" end>My documents</NavLink>
            {isAdmin && <NavLink to="/admin">Admin</NavLink>}
          </nav>
          <div className="nav-user">
            <span>{user.full_name}</span>
            <button className="btn btn-quiet" onClick={() => { logout(); navigate("/login"); }}>
              Log out
            </button>
          </div>
        </>
      )}
    </header>
  );
}
