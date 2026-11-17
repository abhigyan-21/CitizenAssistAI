import { FileText, CheckCircle2, AlertCircle, BookOpen } from "lucide-react";

export default function DocumentSummary({ result }) {
  return (
    <>
      <div className="docket-header">
        <div className="docket-identity">
          <div className="docket-icon">
            <FileText size={20} strokeWidth={1.8} />
          </div>
          <div>
            <h3 className="docket-filename">{result.filename}</h3>
            <div className="docket-specs">
              <span>{result.page_count} page(s) extracted</span>
              <span className="specs-sep">•</span>
              <span>{result.chunk_count} text partitions</span>
              <span className="specs-sep">•</span>
              <span className="specs-hash">ID: {result.document_id}</span>
            </div>
          </div>
        </div>

        <div className="docket-status-group">
          <span className="status-pill status-extracted">
            <CheckCircle2 size={13} strokeWidth={2} />
            Document Successfully Extracted
          </span>
        </div>
      </div>

      {result.warnings?.length > 0 && (
        <div className="civic-alert alert-amber">
          <AlertCircle size={16} className="alert-icon" />
          <div className="alert-content">
            <strong className="alert-title">Document Extraction Notice</strong>
            {result.warnings.map((w, idx) => (
              <p key={idx} className="alert-message">{w}</p>
            ))}
          </div>
        </div>
      )}

      <div className="fidelity-advisory">
        <div className="advisory-title">
          <BookOpen size={14} />
          <span>
            Source Fidelity Status: <strong>{result.source_fidelity_status}</strong>
          </span>
        </div>
        <p className="advisory-text">
          Extraction completed for selectable text layers. Full factual fidelity evaluation and
          cross-verification against legal amendments is performed in later CDTM evaluation stages.
        </p>
      </div>
    </>
  );
}
