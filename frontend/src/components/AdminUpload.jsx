import { useState, useEffect } from "react";
import "./AdminUpload.css";

const ADMIN_PASSWORD = import.meta.env.VITE_ADMIN_PASSWORD || "finbot@admin";

export default function AdminUpload({ api }) {
  const [authed,   setAuthed]   = useState(false);
  const [pwInput,  setPwInput]  = useState("");
  const [pwError,  setPwError]  = useState(false);
  const [file,     setFile]     = useState(null);
  const [status,   setStatus]   = useState(null);
  const [loading,  setLoading]  = useState(false);
  const [docs,     setDocs]     = useState([]);
  const [docsLoad, setDocsLoad] = useState(false);

  // Load doc list once authenticated
  useEffect(() => {
    if (!authed) return;
    fetchDocs();
  }, [authed]);

  async function fetchDocs() {
    setDocsLoad(true);
    try {
      const res  = await fetch(`${api}/docs`);
      const data = await res.json();
      setDocs(data.documents || []);
    } catch {
      setDocs([]);
    } finally {
      setDocsLoad(false);
    }
  }

  function handleLogin() {
    if (pwInput === ADMIN_PASSWORD) {
      setAuthed(true);
      setPwError(false);
    } else {
      setPwError(true);
      setPwInput("");
    }
  }

  async function upload() {
    if (!file) return;
    setLoading(true);
    setStatus(null);

    const form = new FormData();
    form.append("file", file);

    try {
      const res  = await fetch(`${api}/upload`, { method: "POST", body: form });
      const data = await res.json();
      setStatus({ ok: res.ok, msg: data.message || data.error });
      if (res.ok) {
        setFile(null);
        fetchDocs(); // refresh doc list
      }
    } catch {
      setStatus({ ok: false, msg: "Upload failed — server unreachable" });
    } finally {
      setLoading(false);
    }
  }

  // ── Password gate ──
  if (!authed) {
    return (
      <div className="admin-panel">
        <p className="admin-title">🔒 Admin Access</p>
        <input
          type="password"
          className="pw-input"
          placeholder="Enter admin password"
          value={pwInput}
          onChange={e => { setPwInput(e.target.value); setPwError(false); }}
          onKeyDown={e => e.key === "Enter" && handleLogin()}
        />
        {pwError && <p className="pw-error">Incorrect password</p>}
        <button className="upload-btn" onClick={handleLogin}>
          Unlock
        </button>
      </div>
    );
  }

  // ── Admin panel ──
  return (
    <div className="admin-panel">
      <div className="admin-header">
        <p className="admin-title">⚙ Admin Panel</p>
        <button className="logout-btn" onClick={() => { setAuthed(false); setDocs([]); }}>
          Lock
        </button>
      </div>

      {/* Doc list */}
      <div className="doc-list-section">
        <p className="doc-list-label">
          Ingested Documents
          <span className="doc-count">{docsLoad ? "…" : docs.length}</span>
        </p>
        {docs.length === 0 && !docsLoad && (
          <p className="doc-empty">No documents ingested yet</p>
        )}
        {docs.map((d, i) => (
          <div key={i} className="doc-item">
            <span className="doc-icon">📄</span>
            <span className="doc-name">{d}</span>
          </div>
        ))}
      </div>

      {/* Upload */}
      <p className="admin-title" style={{ marginTop: "10px" }}>Upload New PDF</p>
      <label className="file-label">
        <input
          type="file"
          accept=".pdf"
          onChange={e => { setFile(e.target.files[0]); setStatus(null); }}
          style={{ display: "none" }}
        />
        <span className="file-btn">
          {file ? `📄 ${file.name}` : "Choose PDF…"}
        </span>
      </label>

      <button
        className="upload-btn"
        onClick={upload}
        disabled={!file || loading}
      >
        {loading ? "Uploading…" : "Ingest into FinBot"}
      </button>

      {status && (
        <p className={`upload-status ${status.ok ? "ok" : "err"}`}>
          {status.msg}
        </p>
      )}
    </div>
  );
}