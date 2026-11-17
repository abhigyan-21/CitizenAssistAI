import { CheckCircle2, Clock, CircleDot } from "lucide-react";

export const PHASES = [
  {
    id: 1,
    num: "01",
    shortName: "Foundation",
    title: "PDF Upload & Extraction",
    purpose: "Extract text page-by-page with PyMuPDF, chunk boundaries, and flag non-selectable pages.",
  },
  {
    id: 2,
    num: "02",
    shortName: "Retrieval",
    title: "BM25 Lexical Search",
    purpose: "Index document chunks with pure-Python BM25Okapi and retrieve top-k passages for citizen queries.",
  },
  {
    id: 3,
    num: "03",
    shortName: "Grounded Q&A",
    title: "AI-Assisted Q&A",
    purpose: "Generate answers formulated strictly from retrieved passages with verified page-level chunk citations.",
  },
  {
    id: 4,
    num: "04",
    shortName: "Semantic Fidelity",
    title: "Plain-Language Simplification",
    purpose: "Rewrite complex clauses into plain language with two-call AI review auditing condition preservation.",
  },
  {
    id: 5,
    num: "05",
    shortName: "Cross-Lingual",
    title: "Hindi Translation & Term Audit",
    purpose: "Translate clauses to Devanagari Hindi while verifying statutory terms, amounts, dates, and exclusions.",
  },
  {
    id: 6,
    num: "06",
    shortName: "Evaluation Engine",
    title: "CDTM Evaluation Engine",
    purpose: "Execute independent evaluation across all five CDTM dimensions without calculating a composite score.",
  },
  {
    id: 7,
    num: "07",
    shortName: "CDTM Dashboard",
    title: "Multidimensional Dashboard",
    purpose: "Inspect independent dimension cards, evidentiary metrics, and controlled research failure demonstrations.",
  },
  {
    id: 8,
    num: "08",
    shortName: "Comparative Demo",
    title: "Basic vs. CDTM Showcase",
    purpose: "Demonstrate side-by-side contrast between unverified generative AI and audited CDTM governance.",
  },
];

export default function PhaseRoadmap({
  activePhase,
  onSelectPhase,
  documentResult,
  hasSearched,
  hasAsked,
  simplificationResult,
  translationResult,
  evaluationReport,
  qaResultBasic,
  qaResultCDTM,
}) {
  function getRuntimeStatus(phaseId) {
    switch (phaseId) {
      case 1:
        return documentResult ? "completed" : "pending";
      case 2:
        return hasSearched ? "completed" : (documentResult ? "ready" : "pending");
      case 3:
        return hasAsked ? "completed" : (documentResult ? "ready" : "pending");
      case 4:
        return simplificationResult ? "completed" : (documentResult ? "ready" : "pending");
      case 5:
        return translationResult ? "completed" : (documentResult ? "ready" : "pending");
      case 6:
      case 7:
        return evaluationReport ? "completed" : (documentResult ? "ready" : "pending");
      case 8:
        return (qaResultBasic && qaResultCDTM) ? "completed" : (hasAsked ? "ready" : "pending");
      default:
        return "pending";
    }
  }

  return (
    <nav className="roadmap-nav-container" aria-label="Research Demo 8-Phase Walkthrough">
      <div className="roadmap-header-row">
        <div className="roadmap-badge-group">
          <span className="roadmap-tag">RESEARCH ROADMAP</span>
          <span className="roadmap-sub">8-Phase Guided Demonstration</span>
        </div>
        <div className="roadmap-legend">
          <span className="legend-item"><span className="legend-dot dot-completed"></span> Completed</span>
          <span className="legend-item"><span className="legend-dot dot-ready"></span> Ready</span>
          <span className="legend-item"><span className="legend-dot dot-pending"></span> Pending</span>
        </div>
      </div>

      <div className="roadmap-track-scroll">
        <ol className="roadmap-phases-track">
          {PHASES.map((phase) => {
            const runtime = getRuntimeStatus(phase.id);
            const isActive = activePhase === phase.id;

            return (
              <li key={phase.id} className="roadmap-item">
                <button
                  type="button"
                  className={`roadmap-step-btn ${isActive ? "step-btn-active" : ""} step-${runtime}`}
                  onClick={() => onSelectPhase(phase.id)}
                  aria-current={isActive ? "step" : undefined}
                >
                  <div className="step-btn-top">
                    <span className="step-num">{phase.num}</span>
                    <span className={`runtime-status-dot dot-${runtime}`} title={`Runtime status: ${runtime}`} />
                  </div>
                  <div className="step-btn-name">{phase.shortName}</div>
                  <div className="step-btn-footer">
                    <span className="impl-badge">Implemented</span>
                  </div>
                </button>
              </li>
            );
          })}
        </ol>
      </div>
    </nav>
  );
}
