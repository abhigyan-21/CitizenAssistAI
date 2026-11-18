import { ChevronLeft, ChevronRight, FileText } from "lucide-react";
import { PHASES } from "./PhaseRoadmap";

export default function PhaseHeader({
  activePhase,
  onPrevious,
  onNext,
  documentResult,
}) {
  const current = PHASES.find((p) => p.id === activePhase) || PHASES[0];

  return (
    <header className="phase-header-shell">
      <div className="phase-header-main">
        <div className="phase-meta-line">
          <span className="phase-step-indicator">PHASE {current.num} OF 07</span>
          {documentResult && (
            <span className="phase-doc-chip" title={documentResult.filename}>
              <FileText size={12} />
              <span className="doc-chip-name">{documentResult.filename}</span>
              <span className="doc-chip-chunks">({documentResult.total_chunks} chunks)</span>
            </span>
          )}
        </div>
        <h2 className="phase-title">{current.title}</h2>
        <p className="phase-purpose">{current.purpose}</p>
      </div>

      <div className="phase-nav-actions">
        <button
          type="button"
          className="btn btn-nav-step"
          onClick={onPrevious}
          disabled={activePhase <= 1}
          aria-label="Previous Phase"
        >
          <ChevronLeft size={16} />
          <span>Previous</span>
        </button>

        <button
          type="button"
          className="btn btn-nav-step"
          onClick={onNext}
          disabled={activePhase >= 7}
          aria-label="Next Phase"
        >
          <span>Next</span>
          <ChevronRight size={16} />
        </button>
      </div>
    </header>
  );
}
