import { useCallback, useEffect, useState } from "react";
import { deleteAnyDocument, fetchAnyDocumentBlob, listAllDocuments, listUsers, setUserActive } from "../api/admin";
import { errorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";
import DocumentList from "../components/DocumentList";
import PdfViewer from "../components/PdfViewer";

export default function AdminDashboard() {
  const { user: me } = useAuth();
  const [tab, setTab] = useState("users");
  const [users, setUsers] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [ownerFilter, setOwnerFilter] = useState(null); // a user object or null
  const [viewing, setViewing] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const loadUsers = useCallback(async () => setUsers(await listUsers()), []);
  const loadDocs = useCallback(async (ownerId) => setDocuments(await listAllDocuments(ownerId)), []);

  useEffect(() => {
    setLoading(true);
    Promise.all([loadUsers(), loadDocs(ownerFilter?.id)])
      .catch((e) => setError(errorMessage(e, "Could not load admin data.")))
      .finally(() => setLoading(false));
  }, [loadUsers, loadDocs, ownerFilter]);

  const toggleActive = async (u) => {
    const verb = u.is_active ? "Deactivate" : "Activate";
    if (!window.confirm(`${verb} ${u.email}?`)) return;
    try {
      const updated = await setUserActive(u.id, !u.is_active);
      setUsers((list) => list.map((x) => (x.id === u.id ? { ...x, is_active: updated.is_active } : x)));
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  const onDelete = async (doc) => {
    if (!window.confirm(`Delete "${doc.original_filename}" owned by ${doc.owner.email}? This cannot be undone.`)) return;
    try {
      await deleteAnyDocument(doc.id);
      setDocuments((d) => d.filter((x) => x.id !== doc.id));
      loadUsers();
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  const showUserDocs = (u) => {
    setOwnerFilter(u);
    setTab("documents");
  };

  const loadBlob = useCallback(
  () => fetchAnyDocumentBlob(viewing.id),
  [viewing?.id]
);
  return (
    <main className="page">
      <div className="page-head">
        <h1>Administration</h1>
        <div className="tabs" role="tablist">
          <button role="tab" aria-selected={tab === "users"} onClick={() => setTab("users")}>
            Users ({users.length})
          </button>
          <button role="tab" aria-selected={tab === "documents"} onClick={() => setTab("documents")}>
            All documents ({documents.length})
          </button>
        </div>
      </div>
      {error && <p className="error" role="alert">{error}</p>}
      {loading && <p className="status">Loading…</p>}

      {!loading && tab === "users" && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>User</th><th>Role</th><th>Status</th><th>Documents</th><th>Registered</th><th aria-label="Actions" /></tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className={u.is_active ? "" : "inactive"}>
                  <td>{u.full_name}<br /><span className="muted">{u.email}</span></td>
                  <td>{u.role}</td>
                  <td><span className={`pill ${u.is_active ? "pill-ok" : "pill-off"}`}>{u.is_active ? "Active" : "Deactivated"}</span></td>
                  <td>{u.document_count}</td>
                  <td>{new Date(u.created_at).toLocaleDateString()}</td>
                  <td className="actions">
                    <button className="btn" onClick={() => showUserDocs(u)} disabled={u.document_count === 0}>View documents</button>
                    <button className="btn" onClick={() => toggleActive(u)} disabled={u.id === me.id}>
                      {u.is_active ? "Deactivate" : "Activate"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!loading && tab === "documents" && (
        <>
          {ownerFilter && (
            <p className="filter">
              Showing documents uploaded by <strong>{ownerFilter.email}</strong>{" "}
              <button className="btn btn-quiet" onClick={() => setOwnerFilter(null)}>Show all users</button>
            </p>
          )}
          <DocumentList
            documents={documents}
            showOwner
            onView={setViewing}
            onDelete={onDelete}
            emptyText="No documents have been uploaded yet."
          />
        </>
      )}

      {viewing && <PdfViewer title={viewing.original_filename} loadBlob={loadBlob} onClose={() => setViewing(null)} />}
    </main>
  );
}
