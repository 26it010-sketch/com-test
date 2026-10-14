import { useEffect, useState } from "react";
import { errorMessage } from "../api/client";

// `loadBlob` is a function returning a Promise<Blob>, so the same viewer
// works for both the user route and the admin route.
export default function PdfViewer({ title, loadBlob, onClose }) {
  const [url, setUrl] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let objectUrl;
    let cancelled = false;
    loadBlob()
      .then((blob) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setUrl(objectUrl);
      })
      .catch((e) => {
  console.error("PDF loading error:", e);
  console.error("HTTP status:", e?.response?.status);
  console.error("Response data:", e?.response?.data);

  if (!cancelled) {
    setError(errorMessage(e, "Could not load this PDF."));
  }
});
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [loadBlob]);

  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="viewer-backdrop" role="dialog" aria-modal="true" aria-label={title}>
      <div className="viewer">
        <div className="viewer-bar">
          <strong>{title}</strong>
          <button className="btn" onClick={onClose}>Close</button>
        </div>
        {error && <p className="error">{error}</p>}
        {!url && !error && <p className="status">Loading PDF…</p>}
        {url && <iframe title={title} src={url} />}
      </div>
    </div>
  );
}
