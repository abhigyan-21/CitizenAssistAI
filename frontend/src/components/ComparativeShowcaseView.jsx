import { useState } from "react";
import {
  GitCompare,
  Bot,
  Sparkles,
  AlertCircle,
  Shield,
  FileText,
  ChevronDown,
  ChevronUp,
  Download,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";

export default function ComparativeShowcaseView({
  documentId,
  question,
  basicResult,
  cdtmResult,
  evaluationReport,
  retrievedEvidence = [],
  simplificationCount = 0,
  simplificationIssues = 0,
  translationCount = 0,
  translationIssues = 0,
  onGoToQA,
}) {
  const [showEvidence, setShowEvidence] = useState(false);

  const hasAsked = !!(basicResult || cdtmResult);

  function handleExportJSON() {
    const exportData = {
      experiment: "CitizenAssist AI — Comparative Assistance Evaluation Record",
      generated_at_utc: new Date().toISOString(),
      provenance: {
        document_id:
          cdtmResult?.reproducibility?.document_id ||
          basicResult?.reproducibility?.document_id ||
          documentId ||
          "unknown",
        filename:
          cdtmResult?.reproducibility?.filename ||
          basicResult?.reproducibility?.filename ||
          "unknown",
        query: question || "",
        top_k: cdtmResult?.reproducibility?.top_k || 5,
        retrieved_passages_count: retrievedEvidence.length,
      },
      basic_mode: {
        disclaimer:
          "Basic Mode: Unverified baseline generation using the same retrieved source context. Claims are not subject to enforced citation validation, claim-level evidence auditing or CDTM fidelity evaluation.",
        provider_info: basicResult?.provider_info,
        reproducibility: basicResult?.reproducibility,
        answer: basicResult?.answer,
      },
      cdtm_guided_mode: {
        provider_info: cdtmResult?.provider_info,
        reproducibility: cdtmResult?.reproducibility,
        answer: cdtmResult?.answer,
        citations: cdtmResult?.citations || [],
        cited_chunk_ids: cdtmResult?.cited_chunk_ids || [],
      },
      retrieved_evidence: retrievedEvidence,
      cdtm_evaluation_report: evaluationReport,
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const docSlug = (exportData.provenance.document_id || "doc").slice(0, 10);
    link.href = url;
    link.download = `cdtm-comparative-audit-${docSlug}-${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  const groundingStatus = evaluationReport?.evidence_grounding?.status || "not_evaluated";
  const groundingIssues = evaluationReport?.evidence_grounding?.potential_issues || [];
  const unsupportedClaims = evaluationReport?.evidence_grounding?.unsupported_claims || [];
  const allIssues = [...groundingIssues, ...unsupportedClaims];

  const dimensions = [
    {
      name: "Source Fidelity",
      status: evaluationReport?.source_fidelity?.status || "not_evaluated",
      isEvaluated:
        !!evaluationReport?.source_fidelity &&
        evaluationReport.source_fidelity.status !== "not_evaluated",
      detail:
        evaluationReport?.source_fidelity?.status === "verified"
          ? "Compared against rendered document reference."
          : "Automated extraction proxy; unverified until compared with rendered source.",
    },
    {
      name: "Semantic Fidelity",
      status: evaluationReport?.semantic_fidelity?.status || "not_evaluated",
      isEvaluated:
        !!evaluationReport?.semantic_fidelity &&
        evaluationReport.semantic_fidelity.status !== "not_evaluated",
      detail:
        simplificationCount > 0
          ? `${simplificationCount} chunk(s) simplified; ${simplificationIssues} potential condition issue(s) detected.`
          : "No plain-language simplification requested in this session.",
    },
    {
      name: "Evidence Grounding",
      status: groundingStatus,
      isEvaluated: groundingStatus !== "not_evaluated",
      detail:
        allIssues.length > 0
          ? `${allIssues.length} claim-support discrepancy/discrepancies detected by AI review.`
          : cdtmResult?.citations?.length > 0
          ? `${cdtmResult.citations.length} cited passages verified against document store.`
          : "No evidence citations validated for this question.",
    },
    {
      name: "Cross-Lingual Fidelity",
      status: evaluationReport?.cross_lingual_fidelity?.status || "not_evaluated",
      isEvaluated:
        !!evaluationReport?.cross_lingual_fidelity &&
        evaluationReport.cross_lingual_fidelity.status !== "not_evaluated",
      detail:
        translationCount > 0
          ? `${translationCount} translation(s) evaluated; ${translationIssues} term/condition drift issue(s) flagged.`
          : "No Hindi translation evaluated in this session.",
    },
    {
      name: "Citizen Accessibility",
      status: evaluationReport?.accessibility?.status || "not_evaluated",
      isEvaluated:
        !!evaluationReport?.accessibility &&
        evaluationReport.accessibility.status !== "not_evaluated",
      detail:
        "Structural readability and administrative jargon proxies evaluated. Actual citizen comprehension strictly remains not_evaluated pending empirical field study.",
    },
  ];

  return (
    <div className="phase-workbench-shell comparative-showcase-shell">
      {/* Banner */}
      <div className="comp-showcase-hero">
        <div className="showcase-hero-content">
          <span className="hero-tag">PHASE 08 SHOWCASE</span>
          <h3 className="hero-title">Basic AI Assistance vs. CDTM-Guided Assistance</h3>
          <p className="hero-desc">
            Direct experimental comparison: Both paradigms operate on the identical query, document
            context, AI provider, and retrieved passages.
          </p>
        </div>

        <button
          type="button"
          className="btn btn-export-repro"
          onClick={handleExportJSON}
          title="Export complete experimental reproducibility record as JSON"
        >
          <Download size={14} />
          <span>Export Reproducibility Record (JSON)</span>
        </button>
      </div>

      {/* Query Banner */}
      <div className="comp-query-banner">
        <span className="comp-query-label">Active Research Inquiry:</span>
        <p className="comp-query-text">
          {question ? `"${question}"` : "No question submitted in Phase 3 yet."}
        </p>
        {!hasAsked && (
          <button type="button" className="btn btn-secondary btn-sm" onClick={onGoToQA}>
            Go to Phase 3: Ask Question
          </button>
        )}
      </div>

      {/* Side-by-Side Comparison */}
      <div className="comp-columns-grid">
        {/* BASIC AI COLUMN */}
        <article className="comp-column comp-column-basic">
          <header className="comp-col-header">
            <div className="comp-col-identity">
              <Bot size={18} />
              <strong>Basic AI Assistance</strong>
            </div>
            <span className="comp-pill comp-pill-unverified">Unverified Baseline</span>
          </header>

          <div className="comp-disclaimer-box">
            <AlertCircle size={15} />
            <span>
              Basic Mode: Unverified baseline generation using the same retrieved source context.
              Claims are not subject to enforced citation validation, claim-level evidence auditing
              or CDTM fidelity evaluation.
            </span>
          </div>

          <div className="comp-col-text">
            {basicResult?.answer ? (
              <p>{basicResult.answer}</p>
            ) : (
              <p className="comp-empty-state">
                Ask a question in Phase 3 to generate and inspect the Basic AI baseline output.
              </p>
            )}
          </div>

          <footer className="comp-col-footer">
            <span>Model: {basicResult?.provider_info?.model || "AI"}</span>
            <span>Citations: None (Uninspected)</span>
          </footer>
        </article>

        {/* CDTM-GUIDED COLUMN */}
        <article className="comp-column comp-column-cdtm">
          <header className="comp-col-header">
            <div className="comp-col-identity">
              <Sparkles size={18} />
              <strong>CDTM-Guided Assistance</strong>
            </div>
            <span className="comp-pill comp-pill-governed">Audited &amp; Grounded</span>
          </header>

          <div className="comp-grounding-box">
            <Shield size={15} />
            <span>
              Enforces structured grounding: claims reference verified chunk IDs, and the claim-support
              evaluator flags unsupported statements or condition drift.
            </span>
          </div>

          <div className="comp-col-text">
            {cdtmResult?.answer ? (
              <p>{cdtmResult.answer}</p>
            ) : (
              <p className="comp-empty-state">
                Ask a question in Phase 3 to generate and inspect the CDTM-guided output.
              </p>
            )}
          </div>

          <footer className="comp-col-footer">
            <span>Model: {cdtmResult?.provider_info?.model || "AI"}</span>
            <span>Valid Citations: {cdtmResult?.citations?.length || 0} chunk(s) verified</span>
          </footer>
        </article>
      </div>

      {/* Evidentiary Findings */}
      <section className="comp-showcase-section">
        <h4 className="showcase-section-heading">Evidence Grounding &amp; Claim Audit Findings</h4>
        <div className="comp-findings-grid">
          <div className="findings-card">
            <span className="findings-label">Retrieved Evidence Passages</span>
            <strong className="findings-value">{retrievedEvidence.length} passage(s)</strong>
            <button
              type="button"
              className="btn-toggle-evidence"
              onClick={() => setShowEvidence(!showEvidence)}
            >
              <FileText size={14} />
              <span>{showEvidence ? "Hide Passages" : "Inspect Passages"}</span>
              {showEvidence ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>
          </div>

          <div className="findings-card">
            <span className="findings-label">Detected Unsupported Claims / Omissions</span>
            <strong className={`findings-value ${allIssues.length > 0 ? "findings-warn" : ""}`}>
              {allIssues.length} issue(s) detected
            </strong>
            <span className="findings-sub">
              {allIssues.length > 0
                ? "Flagged by claim-support evaluator for expert human inspection."
                : "No claim-level discrepancies flagged in current generation."}
            </span>
          </div>

          <div className="findings-card">
            <span className="findings-label">Transformation Quality Warnings</span>
            <div className="findings-transform-stats">
              <span>Simplification issues: <strong>{simplificationIssues}</strong></span>
              <span>Translation issues: <strong>{translationIssues}</strong></span>
            </div>
            <span className="findings-sub">
              Evaluated via Phase 4 &amp; 5 two-call AI reviewers with deterministic term checks.
            </span>
          </div>
        </div>

        {/* Expandable evidence passages list */}
        {showEvidence && retrievedEvidence.length > 0 && (
          <div className="comp-evidence-drawer">
            <h5 className="drawer-title">Retrieved Passage Pass-Through (Used by both modes):</h5>
            <ul className="drawer-list">
              {retrievedEvidence.map((p, idx) => (
                <li key={p.chunk_id || idx} className="drawer-item">
                  <div className="drawer-item-header">
                    <span className="chunk-tag">{p.chunk_id}</span>
                    <span className="page-tag">Page {p.page_number}</span>
                  </div>
                  <p className="chunk-snippet">{p.text}</p>
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      {/* 5-Dimension CDTM Governance Audit Matrix */}
      <section className="comp-showcase-section">
        <h4 className="showcase-section-heading">CDTM Governance Status Audit (All 5 Dimensions)</h4>
        <div className="comp-dim-table-wrapper">
          <table className="comp-dim-table">
            <thead>
              <tr>
                <th>Dimension</th>
                <th>Evaluation Status</th>
                <th>Audit State</th>
                <th>Auditor Finding &amp; Basis</th>
              </tr>
            </thead>
            <tbody>
              {dimensions.map((dim, idx) => (
                <tr key={idx}>
                  <td className="dim-name-cell">
                    <strong>{dim.name}</strong>
                  </td>
                  <td>
                    <span className={`comp-dim-badge status-${dim.status}`}>
                      {dim.status.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td>
                    {dim.isEvaluated ? (
                      <span className="audit-state evaluated">
                        <CheckCircle2 size={13} /> Evaluated
                      </span>
                    ) : (
                      <span className="audit-state unevaluated">
                        <AlertCircle size={13} /> Unevaluated
                      </span>
                    )}
                  </td>
                  <td className="dim-detail-cell">{dim.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Experimental Reproducibility & Provenance */}
      <section className="comp-showcase-section">
        <h4 className="showcase-section-heading">Experimental Reproducibility &amp; Provenance Record</h4>
        <div className="comp-reproducibility-card">
          <div className="repro-grid">
            <div className="repro-item">
              <span className="repro-key">Document ID:</span>
              <code className="repro-val">
                {cdtmResult?.reproducibility?.document_id ||
                  basicResult?.reproducibility?.document_id ||
                  documentId ||
                  "N/A"}
              </code>
            </div>
            <div className="repro-item">
              <span className="repro-key">Source File:</span>
              <span className="repro-val">
                {cdtmResult?.reproducibility?.filename ||
                  basicResult?.reproducibility?.filename ||
                  "Guidelines.pdf"}
              </span>
            </div>
            <div className="repro-item">
              <span className="repro-key">Basic Provider / Model:</span>
              <span className="repro-val">
                {basicResult?.reproducibility?.provider || "N/A"} (
                {basicResult?.reproducibility?.model || "Standard"})
              </span>
            </div>
            <div className="repro-item">
              <span className="repro-key">CDTM Provider / Model:</span>
              <span className="repro-val">
                {cdtmResult?.reproducibility?.provider || "N/A"} (
                {cdtmResult?.reproducibility?.model || "Configured"})
              </span>
            </div>
            <div className="repro-item">
              <span className="repro-key">Retrieved Passage Pass-Through:</span>
              <span className="repro-val">
                {retrievedEvidence.length} chunks (top_k=
                {cdtmResult?.reproducibility?.top_k || 5})
              </span>
            </div>
            <div className="repro-item">
              <span className="repro-key">Recorded Timestamp (UTC):</span>
              <span className="repro-val">
                {cdtmResult?.reproducibility?.timestamp_utc ||
                  basicResult?.reproducibility?.timestamp_utc ||
                  new Date().toISOString()}
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Regulatory & Research Disclaimer */}
      <div className="comp-mandatory-disclaimer">
        <AlertCircle size={16} />
        <p>
          <strong>Scientific &amp; Regulatory Disclaimer:</strong> CDTM-guided assistance surfaces
          transparent verification signals but does NOT certify administrative or legal truth. AI
          evaluations are aids to human judgment. Citizens and caseworkers must verify entitlements
          against official Central and State government portals.
        </p>
      </div>
    </div>
  );
}
