import { useState } from "react";
import {
  GitCompare,
  X,
  AlertCircle,
  CheckCircle2,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  FileText,
  Shield,
  Bot,
  Sparkles,
  Download,
} from "lucide-react";

export default function ComparativeSummary({
  isOpen,
  onClose,
  question,
  basicResult,
  cdtmResult,
  evaluationReport,
  retrievedEvidence = [],
  simplificationCount = 0,
  simplificationIssues = 0,
  translationCount = 0,
  translationIssues = 0,
}) {
  const [showEvidencePassages, setShowEvidencePassages] = useState(false);

  if (!isOpen) return null;

  function handleExportJSON() {
    const exportData = {
      experiment: "CitizenAssist AI — Comparative Assistance Evaluation Record",
      generated_at_utc: new Date().toISOString(),
      provenance: {
        document_id:
          cdtmResult?.reproducibility?.document_id ||
          basicResult?.reproducibility?.document_id ||
          "unknown",
        filename:
          cdtmResult?.reproducibility?.filename ||
          basicResult?.reproducibility?.filename ||
          "unknown",
        query: question,
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
    const docSlug = exportData.provenance.document_id.slice(0, 10);
    link.href = url;
    link.download = `cdtm-experiment-record-${docSlug}-${Date.now()}.json`;
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
      isEvaluated: !!evaluationReport?.source_fidelity && evaluationReport.source_fidelity.status !== "not_evaluated",
      detail: evaluationReport?.source_fidelity?.status === "verified"
        ? "Compared against rendered document reference."
        : "Automated proxy extraction without manual reference comparison.",
    },
    {
      name: "Semantic Fidelity",
      status: evaluationReport?.semantic_fidelity?.status || "not_evaluated",
      isEvaluated: !!evaluationReport?.semantic_fidelity && evaluationReport.semantic_fidelity.status !== "not_evaluated",
      detail: simplificationCount > 0
        ? `${simplificationCount} chunk(s) simplified; ${simplificationIssues} potential condition issue(s) detected.`
        : "No plain-language simplification requested in this session.",
    },
    {
      name: "Evidence Grounding",
      status: groundingStatus,
      isEvaluated: groundingStatus !== "not_evaluated",
      detail: allIssues.length > 0
        ? `${allIssues.length} claim-support discrepancy/discrepancies detected by AI review.`
        : cdtmResult?.citations?.length > 0
        ? `${cdtmResult.citations.length} cited passages verified against document store.`
        : "No evidence citations validated for this question.",
    },
    {
      name: "Cross-Lingual Fidelity",
      status: evaluationReport?.cross_lingual_fidelity?.status || "not_evaluated",
      isEvaluated: !!evaluationReport?.cross_lingual_fidelity && evaluationReport.cross_lingual_fidelity.status !== "not_evaluated",
      detail: translationCount > 0
        ? `${translationCount} translation(s) evaluated; ${translationIssues} term/condition drift issue(s) flagged.`
        : "No Hindi translation evaluated in this session.",
    },
    {
      name: "Citizen Accessibility",
      status: evaluationReport?.accessibility?.status || "not_evaluated",
      isEvaluated: !!evaluationReport?.accessibility && evaluationReport.accessibility.status !== "not_evaluated",
      detail: "Structural readability and administrative jargon proxies evaluated. Actual citizen comprehension remains not_evaluated pending empirical field study.",
    },
  ];

  return (
    <div className="comp-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="comp-title">
      <div className="comp-modal-card">
        <header className="comp-modal-header">
          <div className="comp-header-title">
            <span className="comp-step-tag">RESEARCH DEMONSTRATION</span>
            <h2 id="comp-title" className="comp-heading">
              <GitCompare size={20} className="comp-title-icon" />
              Comparative Audit: Basic AI vs. CDTM-Guided Assistance
            </h2>
          </div>
          <button
            type="button"
            className="btn-icon-close"
            onClick={onClose}
            aria-label="Close comparative summary"
          >
            <X size={20} />
          </button>
        </header>

        <div className="comp-query-banner">
          <span className="comp-query-label">Evaluation Query:</span>
          <p className="comp-query-text">{question || "No question asked yet."}</p>
        </div>

        <div className="comp-modal-body">
          {/* 1. SIDE-BY-SIDE GENERATION COMPARISON */}
          <section className="comp-section">
            <div className="comp-section-title">
              <span className="section-num">01</span>
              <h3>Dual-Paradigm Generation Comparison</h3>
            </div>
            <p className="comp-section-desc">
              Both models received the exact same query, document context, and provider settings.
              Notice how Basic Mode presents claims without evidentiary attribution.
            </p>

            <div className="comp-columns-grid">
              {/* BASIC COLUMN */}
              <article className="comp-column comp-column-basic">
                <header className="comp-col-header">
                  <div className="comp-col-identity">
                    <Bot size={16} />
                    <strong>Basic AI Output</strong>
                  </div>
                  <span className="comp-pill comp-pill-unverified">Unverified Baseline</span>
                </header>

                <div className="comp-disclaimer-box">
                  <AlertCircle size={14} />
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
                      Basic AI answer has not been generated for this query yet.
                    </p>
                  )}
                </div>

                <footer className="comp-col-footer">
                  <span>Model: {basicResult?.provider_info?.model || "Standard LLM"}</span>
                  <span>Citations: None (Uninspected)</span>
                </footer>
              </article>

              {/* CDTM-GUIDED COLUMN */}
              <article className="comp-column comp-column-cdtm">
                <header className="comp-col-header">
                  <div className="comp-col-identity">
                    <Sparkles size={16} />
                    <strong>CDTM-Guided Output</strong>
                  </div>
                  <span className="comp-pill comp-pill-governed">Audited &amp; Grounded</span>
                </header>

                <div className="comp-grounding-box">
                  <Shield size={14} />
                  <span>
                    Strictly grounded in retrieved passages with chunk-level attribution and
                    claim-support verification.
                  </span>
                </div>

                <div className="comp-col-text">
                  {cdtmResult?.answer ? (
                    <p>{cdtmResult.answer}</p>
                  ) : (
                    <p className="comp-empty-state">
                      CDTM-guided answer has not been generated for this query yet.
                    </p>
                  )}
                </div>

                <footer className="comp-col-footer">
                  <span>Model: {cdtmResult?.provider_info?.model || "Configured LLM"}</span>
                  <span>
                    Valid Citations: {cdtmResult?.citations?.length || 0} chunk(s) verified
                  </span>
                </footer>
              </article>
            </div>
          </section>

          {/* 2. EVIDENTIARY AUDIT & DETECTED DISCREPANCIES */}
          <section className="comp-section">
            <div className="comp-section-title">
              <span className="section-num">02</span>
              <h3>Evidence Grounding &amp; Claim-Support Findings</h3>
            </div>

            <div className="comp-findings-grid">
              <div className="findings-card">
                <span className="findings-label">Retrieved Evidence Passages</span>
                <strong className="findings-value">{retrievedEvidence.length} passage(s)</strong>
                <button
                  type="button"
                  className="btn-toggle-evidence"
                  onClick={() => setShowEvidencePassages(!showEvidencePassages)}
                >
                  <FileText size={14} />
                  <span>{showEvidencePassages ? "Hide Passages" : "Inspect Passages"}</span>
                  {showEvidencePassages ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
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
            {showEvidencePassages && retrievedEvidence.length > 0 && (
              <div className="comp-evidence-drawer">
                <h4 className="drawer-title">Retrieved Passage Pass-Through:</h4>
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

            {allIssues.length > 0 && (
              <div className="comp-issues-tray">
                <div className="issues-tray-header">
                  <AlertTriangle size={16} />
                  <strong>Evaluator Detected Claim Support Discrepancies:</strong>
                </div>
                <ul className="issues-list">
                  {allIssues.map((issue, idx) => (
                    <li key={idx} className="issue-item">
                      {typeof issue === "string" ? issue : issue.claim || issue.description || JSON.stringify(issue)}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </section>

          {/* 3. CDTM MULTIDIMENSIONAL STATUS AUDIT */}
          <section className="comp-section">
            <div className="comp-section-title">
              <span className="section-num">03</span>
              <h3>CDTM Governance Status Audit (All 5 Dimensions)</h3>
            </div>
            <p className="comp-section-desc">
              Each dimension is evaluated on its own merits. No composite or weighted trust score is
              ever calculated.
            </p>

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

          {/* 4. EXPERIMENTAL REPRODUCIBILITY & PROVENANCE RECORD */}
          <section className="comp-section">
            <div className="comp-section-title">
              <span className="section-num">04</span>
              <h3>Experimental Reproducibility &amp; Provenance Record</h3>
            </div>
            <p className="comp-section-desc">
              Exact generation parameters, model identifiers, and execution timestamps recorded to
              support scientific verification and independent audit.
            </p>

            <div className="comp-reproducibility-card">
              <div className="repro-grid">
                <div className="repro-item">
                  <span className="repro-key">Document ID:</span>
                  <code className="repro-val">
                    {cdtmResult?.reproducibility?.document_id ||
                      basicResult?.reproducibility?.document_id ||
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

          {/* RESEARCH DISCLAIMER */}
          <div className="comp-mandatory-disclaimer">
            <AlertCircle size={16} />
            <p>
              <strong>Scientific &amp; Regulatory Disclaimer:</strong> CDTM-guided assistance surfaces
              transparent verification signals but does NOT certify administrative or legal truth.
              AI evaluations are aids to human judgment. Citizens and caseworkers must verify
              entitlements against official Central and State government portals.
            </p>
          </div>
        </div>

        <footer className="comp-modal-footer">
          <button
            type="button"
            className="btn btn-export-repro"
            onClick={handleExportJSON}
          >
            <Download size={14} /> Export Reproducibility Record (JSON)
          </button>
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            Close Comparative Audit
          </button>
        </footer>
      </div>
    </div>
  );
}
