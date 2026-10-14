const fmtSize = (b) => (b < 1024 * 1024 ? `${Math.max(1, Math.round(b / 1024))} KB` : `${(b / 1024 / 1024).toFixed(1)} MB`);
const fmtDate = (d) => new Date(d).toLocaleString();

export default function DocumentList({ documents, onView, onDelete, showOwner = false, emptyText }) {
  if (documents.length === 0) return <p className="empty">{emptyText}</p>;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>File</th>
            {showOwner && <th>Owner</th>}
            <th>Size</th>
            <th>Uploaded</th>
            <th aria-label="Actions" />
          </tr>
        </thead>
        <tbody>
          {documents.map((d) => (
            <tr key={d.id}>
              <td className="filename">{d.original_filename}</td>
              {showOwner && (
                <td>
                  {d.owner.full_name}
                  <br />
                  <span className="muted">{d.owner.email}</span>
                </td>
              )}
              <td>{fmtSize(d.size_bytes)}</td>
              <td>{fmtDate(d.uploaded_at)}</td>
              <td className="actions">
                <button className="btn" onClick={() => onView(d)}>View</button>
                <button className="btn btn-danger" onClick={() => onDelete(d)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
