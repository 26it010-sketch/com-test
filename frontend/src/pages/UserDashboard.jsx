import { useCallback, useEffect, useRef, useState } from "react";
import { deleteDocument, fetchDocumentBlob, listDocuments, uploadDocument } from "../api/documents";
import { errorMessage } from "../api/client";
import DocumentList from "../components/DocumentList";
import PdfViewer from "../components/PdfViewer";

const MAX_MB = 10; // keep in sync with the backend MAX_UPLOAD_SIZE_MB; the server is the real gatekeeper

export default function UserDashboard() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [progress, setProgress] = useState(null);
  const [viewing, setViewing] = useState(null);
  const fileInput = useRef(null);

  const refresh = useCallback(async () => {
    try {
      setDocuments(await listDocuments());
    } catch (e) {
      setError(errorMessage(e, "Could not load your documents."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const onFile = async (e) => {
    const file = e.target.files[0];
    e.target.value = "";
    if (!file) return;
    setError("");
    if (!file.name.toLowerCase().endsWith(".pdf")) return setError("Only PDF files can be uploaded.");
    if (file.size > MAX_MB * 1024 * 1024) return setError(`That file is larger than ${MAX_MB} MB.`);
    try {
      setProgress(0);
      await uploadDocument(file, setProgress);
      await refresh();
    } catch (err) {
      setError(errorMessage(err, "Upload failed."));
    } finally {
      setProgress(null);
    }
  };

  const onDelete = async (doc) => {
    if (!window.confirm(`Delete "${doc.original_filename}"? This cannot be undone.`)) return;
    try {
      await deleteDocument(doc.id);
      setDocuments((docs) => docs.filter((d) => d.id !== doc.id));
    } catch (err) {
      setError(errorMessage(err, "Could not delete the document."));
    }
  };

  const loadBlob = useCallback(() => fetchDocumentBlob(viewing.id), [viewing]);

  return (
    <main className="page">
      <div className="page-head">
        <h1>My documents</h1>
        <div>
          <input ref={fileInput} type="file" accept="application/pdf,.pdf" hidden onChange={onFile} />
          <button className="btn btn-primary" onClick={() => fileInput.current.click()} disabled={progress !== null}>
            {progress !== null ? `Uploading ${progress}%` : "Upload PDF"}
          </button>
        </div>
      </div>
      {error && <p className="error" role="alert">{error}</p>}
      {loading ? (
        <p className="status">Loading…</p>
      ) : (
        <DocumentList
          documents={documents}
          onView={setViewing}
          onDelete={onDelete}
          emptyText={`No documents yet. Upload a PDF up to ${MAX_MB} MB to get started.`}
        />
      )}
      {viewing && <PdfViewer title={viewing.original_filename} loadBlob={loadBlob} onClose={() => setViewing(null)} />}
    </main>
  );
}
