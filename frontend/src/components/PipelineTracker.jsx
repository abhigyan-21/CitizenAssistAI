import { CheckCircle2, AlertTriangle, Clock, ShieldCheck, ArrowRight } from "lucide-react";

/**
 * Maps status string to human-friendly label and css classes.
 */
function getStageBadge(status) {
  switch (status) {
    case "completed":
      return {
        label: "Completed",
        icon: <CheckCircle2 size={13} />,
        className: "badge-completed",
      };
    case "ready":
      return {
        label: "Ready",
        icon: <Clock size={13} />,
        className: "badge-ready",
      };
    case "requires_review":
      return {
        label: "Review Flag",
        icon: <AlertTriangle size={13} />,
        className: "badge-warning",
      };
    case "idle":
    default:
      return {
        label: "Pending",
        icon: <Clock size={13} />,
        className: "badge-idle",
      };
  }
}

/**
 * Maps CDTM evaluation dimension status to visual pill styling.
 */
function getCDTMStatusBadge(status) {
  if (!status || status === "not_evaluated") {
    return { label: "Not Evaluated", className: "cdtm-pill-neutral" };
  }
  const s = String(status).toLowerCase();
  if (s === "verified" || s === "grounded") {
    return { label: s === "grounded" ? "Grounded" : "Verified", className: "cdtm-pill-success" };
  }
  if (s === "potential_issue" || s === "partially_grounded" || s === "requires_review") {
    return {
      label: s === "partially_grounded" ? "Partially Grounded" : "Review Recommended",
      className: "cdtm-pill-warning",
    };
  }
  if (s === "requires_human_review") {
    return { label: "Requires Expert Review", className: "cdtm-pill-navy" };
  }
  if (s === "ungrounded") {
    return { label: "Ungrounded", className: "cdtm-pill-danger" };
  }
  return { label: status, className: "cdtm-pill-neutral" };
}

export default function PipelineTracker({
  documentResult,
  hasAsked,
  qaResult,
  simplificationCount = 0,
  simplificationIssues = 0,
  translationCount = 0,
  translationIssues = 0,
  evaluationReport = null,
}) {
  // Determine processing pipeline statuses
  const extractionStatus = documentResult
    ? (documentResult.warnings?.length > 0 ? "requires_review" : "completed")
    : "idle";

  const indexingStatus = documentResult?.total_chunks > 0 ? "completed" : "idle";

  const qaStatus = hasAsked
    ? (qaResult?.insufficient_evidence ? "requires_review" : "completed")
    : (indexingStatus === "completed" ? "ready" : "idle");

  const simplificationStatus = simplificationCount > 0
    ? (simplificationIssues > 0 ? "requires_review" : "completed")
    : "idle";

  const translationStatus = translationCount > 0
    ? (translationIssues > 0 ? "requires_review" : "completed")
    : "idle";

  const pipelineStages = [
    { id: 1, name: "PDF Extraction", desc: "PyMuPDF text extraction", status: extractionStatus },
    { id: 2, name: "BM25 Indexing", desc: "Lexical chunk indexing", status: indexingStatus },
    { id: 3, name: "Evidence Q&A", desc: "Passage retrieval & answer", status: qaStatus },
    { id: 4, name: "Simplification", desc: "Plain-language plain rewrite", status: simplificationStatus },
    { id: 5, name: "Hindi Translation", desc: "Devanagari cross-lingual", status: translationStatus },
  ];

  // CDTM Evaluation Dimensions (Evaluated independently)
  const cdtmDimensions = [
    {
      name: "Source Fidelity",
      status: evaluationReport?.source_fidelity?.status || "not_evaluated",
      note: "PDF structural integrity & selectable text",
    },
    {
      name: "Semantic Fidelity",
      status: evaluationReport?.semantic_fidelity?.status || "not_evaluated",
      note: "Condition & exclusion preservation",
    },
    {
      name: "Evidence Grounding",
      status: evaluationReport?.evidence_grounding?.status || "not_evaluated",
      note: "Claim-level support in cited passages",
    },
    {
      name: "Cross-Lingual Fidelity",
      status: evaluationReport?.cross_lingual_fidelity?.status || "not_evaluated",
      note: "Hindi terminology & number consistency",
    },
    {
      name: "Citizen Accessibility",
      status: evaluationReport?.accessibility?.status || "not_evaluated",
      note: "Structural readability & jargon check (proxy only)",
    },
  ];

  return (
    <section className="pipeline-tracker-box">
      <header className="tracker-header">
        <div className="tracker-title-row">
          <span className="tracker-phase-tag">LIVE PIPELINE AUDIT</span>
          <h3 className="tracker-heading">Document Pipeline &amp; CDTM Evaluation Tracks</h3>
        </div>
        <span className="tracker-badge">
          <ShieldCheck size={14} /> Dual-Track Verification
        </span>
      </header>

      {/* TRACK 1: Document Processing Pipeline */}
      <div className="track-container">
        <div className="track-label-bar">
          <span className="track-name">Track A · Document Processing Pipeline</span>
          <span className="track-subtext">Sequential operational stages</span>
        </div>
        <ol className="pipeline-stages-list">
          {pipelineStages.map((stage, idx) => {
            const badge = getStageBadge(stage.status);
            return (
              <li key={stage.id} className={`pipeline-stage-item stage-${stage.status}`}>
                <div className="stage-top">
                  <span className="stage-step-num">0{stage.id}</span>
                  <span className={`stage-status-pill ${badge.className}`}>
                    {badge.icon}
                    <span>{badge.label}</span>
                  </span>
                </div>
                <div className="stage-body">
                  <h4 className="stage-name">{stage.name}</h4>
                  <p className="stage-desc">{stage.desc}</p>
                </div>
                {idx < pipelineStages.length - 1 && (
                  <ArrowRight size={14} className="stage-connector" aria-hidden="true" />
                )}
              </li>
            );
          })}
        </ol>
      </div>

      {/* TRACK 2: Independent CDTM Evaluation Track */}
      <div className="track-container track-cdtm">
        <div className="track-label-bar">
          <span className="track-name">Track B · CDTM Multi-Dimensional Governance</span>
          <span className="track-subtext">
            Independent evaluation dimensions · No composite score
          </span>
        </div>
        <div className="cdtm-track-grid">
          {cdtmDimensions.map((dim, idx) => {
            const badge = getCDTMStatusBadge(dim.status);
            return (
              <div key={idx} className="cdtm-track-card">
                <div className="cdtm-card-header">
                  <span className="cdtm-card-dim-name">{dim.name}</span>
                  <span className={`cdtm-mini-badge ${badge.className}`}>{badge.label}</span>
                </div>
                <p className="cdtm-card-note">{dim.note}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
