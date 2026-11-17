import { useState } from "react";
import { ShieldCheck, RotateCw, ChevronDown, ChevronUp, AlertCircle, FileCode, CheckCircle2 } from "lucide-react";

export default function EvaluationEngineView({
  documentId,
  evaluationReport,
  onRefresh,
  isRefreshing,
}) {
  const [showRawJson, setShowRawJson] = useState(false);

  if (!evaluationReport) {
    return (
      <div className="civic-card state-notice loading-state">
        <p>Awaiting evaluation report from backend CDTM engine…</p>
      </div>
    );
  }

  const dimensions = [
    {
      id: "source_fidelity",
      name: "1. Source Fidelity",
      status: evaluationReport.source_fidelity?.status || "not_evaluated",
      summary: evaluationReport.source_fidelity?.summary || "No extraction warnings recorded.",
      metrics: [
        { label: "Total Pages", val: evaluationReport.source_fidelity?.total_pages ?? "N/A" },
        { label: "Empty / Image Pages", val: evaluationReport.source_fidelity?.empty_pages?.length ?? 0 },
        { label: "Extraction Warnings", val: evaluationReport.source_fidelity?.warnings?.length ?? 0 },
      ],
      note: "Clean extraction without warnings remains not_evaluated until compared against rendered reference.",
    },
    {
      id: "semantic_fidelity",
      name: "2. Semantic Fidelity",
      status: evaluationReport.semantic_fidelity?.status || "not_evaluated",
      summary: evaluationReport.semantic_fidelity?.summary || "Evaluates plain-language condition preservation.",
      metrics: [
        { label: "Evaluated Chunks", val: evaluationReport.semantic_fidelity?.evaluated_chunks_count ?? 0 },
        { label: "Preserved Conditions", val: evaluationReport.semantic_fidelity?.preserved_conditions_count ?? 0 },
        { label: "Condition Divergences", val: evaluationReport.semantic_fidelity?.issues_count ?? 0 },
      ],
      note: "Two-call review auditing whether plain English simplification altered statutory conditions.",
    },
    {
      id: "evidence_grounding",
      name: "3. Evidence Grounding",
      status: evaluationReport.evidence_grounding?.status || "not_evaluated",
      summary: evaluationReport.evidence_grounding?.summary || "Audits claim-level support against cited passages.",
      metrics: [
        { label: "Cited Chunk Passages", val: evaluationReport.evidence_grounding?.cited_chunks_count ?? 0 },
        { label: "Supported Claims", val: evaluationReport.evidence_grounding?.supported_claims_count ?? "N/A" },
        { label: "Unsupported Assertions", val: evaluationReport.evidence_grounding?.unsupported_claims?.length ?? 0 },
      ],
      note: "Valid citation IDs alone do NOT prove support; AI review audits atomic factual claims.",
    },
    {
      id: "cross_lingual_fidelity",
      name: "4. Cross-Lingual Fidelity",
      status: evaluationReport.cross_lingual_fidelity?.status || "not_evaluated",
      summary: evaluationReport.cross_lingual_fidelity?.summary || "Audits English-Hindi terminology and numeral consistency.",
      metrics: [
        { label: "Evaluated Translations", val: evaluationReport.cross_lingual_fidelity?.evaluated_translations_count ?? 0 },
        { label: "Preserved Entities", val: evaluationReport.cross_lingual_fidelity?.preserved_entities_count ?? "N/A" },
        { label: "Terminology Drift", val: evaluationReport.cross_lingual_fidelity?.drift_count ?? 0 },
      ],
      note: "Deterministic numerals and dates verified separately from semantic condition review.",
    },
    {
      id: "accessibility",
      name: "5. Citizen Accessibility (Structural Proxy)",
      status: evaluationReport.accessibility?.status || "not_evaluated",
      summary: evaluationReport.accessibility?.summary || "Computes English readability, sentence complexity, and administrative jargon.",
      metrics: [
        { label: "Flesch Reading Ease", val: evaluationReport.accessibility?.metrics?.flesch_reading_ease ?? "N/A" },
        { label: "Grade Level", val: evaluationReport.accessibility?.metrics?.flesch_kincaid_grade ?? "N/A" },
        { label: "Jargon / Acronyms", val: evaluationReport.accessibility?.metrics?.administrative_jargon_count ?? "N/A" },
      ],
      note: "Readability proxies only. Actual citizen comprehension strictly remains not_evaluated pending empirical citizen studies.",
    },
  ];

  return (
    <div className="phase-workbench-shell">
      {/* Banner: Invariant reminder */}
      <div className="cdtm-invariant-banner">
        <ShieldCheck size={18} className="banner-icon" />
        <div>
          <strong>CDTM Architecture Invariant:</strong> Five independent evaluation reports. No
          composite, weighted, or aggregate trust score is ever computed.
        </div>
      </div>

      <div className="workbench-top-bar">
        <span className="top-bar-title">CDTM Evaluation Engine Diagnostic Reports</span>
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={onRefresh}
          disabled={isRefreshing}
        >
          <RotateCw size={13} className={isRefreshing ? "spin-icon" : ""} />
          <span>{isRefreshing ? "Re-evaluating Engine…" : "Refresh Engine Reports"}</span>
        </button>
      </div>

      {/* Grid of the 5 Dimension Reports */}
      <div className="engine-reports-grid">
        {dimensions.map((dim) => (
          <article key={dim.id} className="engine-report-card">
            <header className="report-card-header">
              <span className="report-card-title">{dim.name}</span>
              <span className={`status-pill status-${dim.status}`}>
                {dim.status.replace(/_/g, " ")}
              </span>
            </header>

            <p className="report-card-summary">{dim.summary}</p>

            <div className="report-metrics-row">
              {dim.metrics.map((m, idx) => (
                <div key={idx} className="metric-chip">
                  <span className="metric-chip-label">{m.label}:</span>
                  <strong className="metric-chip-val">{m.val}</strong>
                </div>
              ))}
            </div>

            <footer className="report-card-footer">
              <span className="report-card-note">{dim.note}</span>
            </footer>
          </article>
        ))}
      </div>

      {/* Collapsible Raw API Report JSON */}
      <div className="workbench-collapsible-section">
        <button
          type="button"
          className="btn-toggle-collapsible"
          onClick={() => setShowRawJson(!showRawJson)}
        >
          <FileCode size={14} />
          <span>Inspect Raw Evaluation Engine JSON Response</span>
          {showRawJson ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
        </button>

        {showRawJson && (
          <div className="collapsible-drawer-content">
            <pre className="raw-json-block">
              {JSON.stringify(evaluationReport, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
