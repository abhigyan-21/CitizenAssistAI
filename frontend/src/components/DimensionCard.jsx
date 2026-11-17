import { useState } from "react";
import {
  CheckCircle2,
  AlertCircle,
  Clock,
  HelpCircle,
  XCircle,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

/**
 * DimensionCard
 *
 * Reusable card representing one of the five CDTM dimensions.
 *
 * Status Colour Mapping (Strictly Enforced):
 *   Verified / Grounded                            -> Forest green
 *   Potential Issue / Divergence / Partially Grounded -> Amber
 *   Requires Human Review                          -> Navy
 *   Requires Review                                -> Amber
 *   Ungrounded                                     -> Red
 *   Not Evaluated                                  -> Neutral slate
 *
 * Invariant: Citizen Accessibility is never shown as verified based on readability proxies.
 */

export function mapStatusConfig(status, dimensionKey = "") {
  const norm = (status || "not_evaluated").toLowerCase();

  switch (norm) {
    case "verified":
    case "grounded":
      return {
        label: norm === "grounded" ? "Grounded" : "Verified",
        colorClass: "badge-status-green",
        borderClass: "card-border-green",
        icon: <CheckCircle2 size={13} strokeWidth={2} />,
      };
    case "partially_grounded":
    case "potential_issue":
    case "divergence":
    case "partial":
    case "requires_review":
      return {
        label:
          norm === "partially_grounded"
            ? "Partially Grounded"
            : norm === "potential_issue"
            ? "Potential Issue"
            : norm === "requires_review"
            ? "Requires Review"
            : "Divergence Detected",
        colorClass: "badge-status-amber",
        borderClass: "card-border-amber",
        icon: <AlertCircle size={13} strokeWidth={2} />,
      };
    case "requires_human_review":
      return {
        label: "Requires Human Review",
        colorClass: "badge-status-navy",
        borderClass: "card-border-navy",
        icon: <Clock size={13} strokeWidth={2} />,
      };
    case "ungrounded":
      return {
        label: "Ungrounded",
        colorClass: "badge-status-red",
        borderClass: "card-border-red",
        icon: <XCircle size={13} strokeWidth={2} />,
      };
    case "abstained":
      return {
        label: "Abstained (Insufficient Evidence)",
        colorClass: "badge-status-navy",
        borderClass: "card-border-navy",
        icon: <Clock size={13} strokeWidth={2} />,
      };
    case "not_evaluated":
    default:
      return {
        label: "Not Evaluated",
        colorClass: "badge-status-neutral",
        borderClass: "card-border-neutral",
        icon: <HelpCircle size={13} strokeWidth={2} />,
      };
  }
}

export default function DimensionCard({
  dimensionKey,
  dimensionCode,
  title,
  subtitle,
  result,
}) {
  const [expanded, setExpanded] = useState(false);

  const status = result?.status || "not_evaluated";
  const config = mapStatusConfig(status, dimensionKey);

  return (
    <article className={`dimension-card ${config.borderClass}`}>
      <header className="dimension-card-header">
        <div className="dimension-identity">
          <span className="dimension-code">{dimensionCode}</span>
          <h4 className="dimension-title">{title}</h4>
        </div>
        <span className={`status-pill ${config.colorClass}`}>
          {config.icon}
          {config.label}
        </span>
      </header>

      <p className="dimension-subtitle">{subtitle}</p>

      {/* Primary Highlights */}
      <div className="dimension-summary-metrics">
        {dimensionKey === "source_fidelity" && result && (
          <div className="metric-row">
            <span>Pages with text: <strong>{result.pages_with_text ?? 0} / {result.page_count ?? 0}</strong></span>
            {result.has_reference_comparison ? (
              <span className="metric-tag">Reference comparison: {result.reference_match ? "Matched" : "Mismatch"}</span>
            ) : (
              <span className="metric-tag subtle">Uncompared against visual ground truth</span>
            )}
          </div>
        )}

        {dimensionKey === "semantic_fidelity" && result && (
          <div className="metric-row">
            <span>Preserved conditions: <strong>{result.preserved_conditions?.length ?? 0}</strong></span>
            <span>Flagged missing: <strong>{result.potentially_missing?.length ?? 0}</strong></span>
          </div>
        )}

        {dimensionKey === "evidence_grounding" && result && (
          <div className="metric-row">
            <span>Supported claims: <strong>{result.supported_claims_count ?? 0}</strong></span>
            <span>Unsupported claims: <strong>{result.unsupported_claims_count ?? 0}</strong></span>
            <span>Cited passages: <strong>{result.valid_chunk_ids?.length ?? 0}</strong></span>
          </div>
        )}

        {dimensionKey === "cross_lingual_fidelity" && result && (
          <div className="metric-row">
            <span>Preserved terms: <strong>{result.preserved_terms?.length ?? 0}</strong></span>
            <span>Flagged divergences: <strong>{result.potentially_divergent?.length ?? 0}</strong></span>
          </div>
        )}

        {dimensionKey === "citizen_accessibility" && result?.proxy_metrics && (
          <div className="metric-row">
            {result.proxy_metrics.flesch_reading_ease !== null ? (
              <span>Reading Ease: <strong>{result.proxy_metrics.flesch_reading_ease} / 100</strong> ({result.proxy_metrics.readability_category})</span>
            ) : (
              <span>Hindi Structural Complexity: <strong>{result.proxy_metrics.readability_category}</strong></span>
            )}
            {result.proxy_metrics.unexplained_acronyms?.length > 0 && (
              <span className="metric-alert-tag">Unexplained acronyms: {result.proxy_metrics.unexplained_acronyms.join(", ")}</span>
            )}
          </div>
        )}
      </div>

      {/* Expand/Collapse Toggle */}
      <button
        type="button"
        className="btn-toggle-evidence"
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
      >
        <span>{expanded ? "Hide Supporting Evidence & Notes" : "View Supporting Evidence & Limitations"}</span>
        {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {/* Expandable Evidence Drawer */}
      {expanded && (
        <div className="dimension-evidence-drawer">
          {/* Methodological limitations / note */}
          {result?.note && (
            <div className="evidence-note-block">
              <span className="evidence-note-label">Evaluation Note:</span>
              <p className="evidence-note-text">{result.note}</p>
            </div>
          )}

          {/* Specific dimension details */}
          {dimensionKey === "source_fidelity" && result?.warnings?.length > 0 && (
            <div className="drawer-item-list">
              <span className="drawer-section-title">Extraction Warnings:</span>
              <ul>
                {result.warnings.map((w, idx) => (
                  <li key={idx} className="warning-text">{w}</li>
                ))}
              </ul>
            </div>
          )}

          {dimensionKey === "semantic_fidelity" && (
            <>
              {result?.potentially_missing?.length > 0 && (
                <div className="drawer-item-list">
                  <span className="drawer-section-title warning-heading">Flagged Missing or Altered Conditions:</span>
                  <ul>
                    {result.potentially_missing.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
              {result?.preserved_conditions?.length > 0 && (
                <div className="drawer-item-list">
                  <span className="drawer-section-title success-heading">Confirmed Preserved Conditions:</span>
                  <ul>
                    {result.preserved_conditions.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}

          {dimensionKey === "evidence_grounding" && result?.claims?.length > 0 && (
            <div className="drawer-item-list">
              <span className="drawer-section-title">Claim-Level Audit:</span>
              <ul className="claims-list">
                {result.claims.map((c, idx) => (
                  <li key={idx} className={`claim-entry ${c.supported ? "claim-supported" : "claim-unsupported"}`}>
                    <span className="claim-statement">"{c.claim}"</span>
                    <span className="claim-verdict">{c.supported ? "Supported by passage" : "Unsupported"}</span>
                    {c.reasoning && <p className="claim-reasoning">{c.reasoning}</p>}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {dimensionKey === "cross_lingual_fidelity" && (
            <>
              {result?.potentially_divergent?.length > 0 && (
                <div className="drawer-item-list">
                  <span className="drawer-section-title warning-heading">Potential Translation Divergences:</span>
                  <ul>
                    {result.potentially_divergent.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
              {result?.preserved_terms?.length > 0 && (
                <div className="drawer-item-list">
                  <span className="drawer-section-title success-heading">Confirmed Preserved Terms:</span>
                  <ul>
                    {result.preserved_terms.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}

          {dimensionKey === "citizen_accessibility" && result?.proxy_metrics && (
            <div className="drawer-item-list">
              <span className="drawer-section-title">Structural Accessibility Proxies:</span>
              <div className="proxy-details-grid">
                <div>Sentence count: <strong>{result.proxy_metrics.sentence_count}</strong></div>
                <div>Word count: <strong>{result.proxy_metrics.word_count}</strong></div>
                <div>Avg sentence length: <strong>{result.proxy_metrics.avg_sentence_length} words</strong></div>
                {result.proxy_metrics.flesch_kincaid_grade !== null && (
                  <div>Flesch-Kincaid Grade: <strong>Grade {result.proxy_metrics.flesch_kincaid_grade}</strong></div>
                )}
              </div>
              {result.proxy_metrics.unexplained_administrative_terms?.length > 0 && (
                <div className="terms-warning-block">
                  <span className="warning-heading">Administrative terms requiring contextual explanation:</span>
                  <ul>
                    {result.proxy_metrics.unexplained_administrative_terms.map((t, idx) => (
                      <li key={idx}>{t}</li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="empirical-study-notice">
                <strong>Empirical Study Constraint:</strong> Genuine citizen comprehension cannot be validated through automated formulas. Actual accessibility remains <em>not_evaluated</em> until empirical user studies are completed.
              </div>
            </div>
          )}
        </div>
      )}
    </article>
  );
}
