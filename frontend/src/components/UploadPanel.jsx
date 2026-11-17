import { FileUp, AlertCircle } from "lucide-react";

export default function UploadPanel({ file, busy, error, onFileChange, onSubmit }) {
  return (
    <section className="civic-card intake-card">
      <div className="card-header">
        <div>
          <span className="card-step">PHASE 01</span>
          <h2 className="card-title">Document Intake</h2>
        </div>
        <span className="status-label">PDF Extraction</span>
      </div>

      <form onSubmit={onSubmit} className="intake-form">
        <label className="intake-dropzone">
          <input
            type="file"
            accept="application/pdf,.pdf"
            onChange={(e) => onFileChange(e.target.files?.[0] || null)}
          />
          <span className="dropzone-icon">
            <FileUp size={24} strokeWidth={1.8} />
          </span>
          <div className="dropzone-text">
            <strong className="dropzone-file-name">
              {file ? file.name : "Select an administrative PDF document"}
            </strong>
            <span className="dropzone-hint">
              {file
                ? `${(file.size / 1048576).toFixed(2)} MB · Ready for processing`
                : "Standard PDF format · Maximum upload limit 20 MB"}
            </span>
          </div>
          <span className="dropzone-action">Browse filesystem</span>
        </label>

        {error && (
          <div className="civic-alert alert-error">
            <AlertCircle size={16} className="alert-icon" />
            <span>{error}</span>
          </div>
        )}

        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={!file || busy}>
            {busy ? "Extracting Document..." : file ? "Extract Document Text" : "Select a PDF to enable"}
          </button>
        </div>
      </form>
    </section>
  );
}
