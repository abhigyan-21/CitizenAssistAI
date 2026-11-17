import { FileUp, AlertCircle } from "lucide-react";

export default function PhasePromptDocRequired({ onGoToUpload }) {
  return (
    <div className="civic-card prompt-doc-card">
      <div className="prompt-doc-icon">
        <FileUp size={32} />
      </div>
      <h3 className="prompt-doc-title">Document Context Required</h3>
      <p className="prompt-doc-desc">
        This research phase operates on extracted document partitions. Please upload and extract an
        administrative PDF in <strong>Phase 1: Foundation</strong> before proceeding.
      </p>
      <button type="button" className="btn btn-primary" onClick={onGoToUpload}>
        Go to Phase 1: Upload Document
      </button>
    </div>
  );
}
