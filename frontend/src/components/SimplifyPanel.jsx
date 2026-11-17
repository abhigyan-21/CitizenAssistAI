import { AlertCircle, X } from "lucide-react";
import FidelityBadge from "./FidelityBadge";
import SimplificationQualityBadge from "./SimplificationQualityBadge";

/**
 * SimplifyPanel
 *
 * Displays the simplification result with TWO independent assessment rows:
 *
 *   Row 1 — Simplification Quality (deterministic, difflib.SequenceMatcher)
 *            Did the output actually change from the source?
 *
 *   Row 2 — Semantic Fidelity (AI-assisted, Call 2)
 *            Were meaning, conditions, amounts and dates preserved?
 *
 * These two results must never be merged into a single verdict.
 */

const QUALITY_NOTICES = {
  insufficient: {
    className: "civic-alert alert-amber simplify-quality-notice",
    text:
      "The simplified text is very similar to the source passage and may not be meaningfully simplified. " +
      "Review it manually before use.",
  },
  requires_human_review: {
    className: "civic-alert alert-amber simplify-quality-notice",
    text:
      "The source passage is short. The similarity score may not reliably indicate whether simplification occurred. " +
      "Human review is recommended.",
  },
  error: {
    className: "civic-alert alert-error simplify-quality-notice",
    text:
      "The AI model failed to produce a valid plain-language simplification. " +
      "Evaluation could not be performed. Please verify your AI provider configuration or retry.",
  },
};

export default function SimplifyPanel({
  result,
  onClose,
  onRetry,
  onTranslateSimplified,
}) {
  if (!result) return null;

  const {
    source_passage,
    simplified_text,
    simplification_quality,
    similarity_score,
    fidelity,
    controlled_demo,
  } = result;

  const qualityNotice = QUALITY_NOTICES[simplification_quality] ?? null;
  const isError = simplification_quality === "error";
  const similarityPct =
    typeof similarity_score === "number" && !isError
      ? `${(similarity_score * 100).toFixed(0)}%`
      : null;

  return (
    <div className="simplify-panel">
      <div className="simplify-panel-header">
        {/* Title + badge rows — quality and fidelity shown separately */}
        <div className="simplify-panel-title-col">
          <span className="simplify-panel-label">Plain-Language Simplification</span>

          {/* Row 1: Simplification Quality (deterministic check) */}
          <div className="simplify-assessment-row">
            <span className="simplify-assessment-key">Simplification quality</span>
            <SimplificationQualityBadge quality={simplification_quality} />
          </div>

          {/* Row 2: Semantic Fidelity (AI-assisted, meaning preservation only) */}
          <div className="simplify-assessment-row">
            <span className="simplify-assessment-key">Semantic fidelity</span>
            <FidelityBadge status={fidelity.status} controlled_demo={controlled_demo} />
          </div>

          {/* Similarity score — diagnostic metadata, not a quality verdict */}
          {similarityPct && (
            <div className="similarity-score-line">
              Similarity to source: {similarityPct}
              {" "}(lower = more simplified; threshold ≥ 85% flags insufficient)
            </div>
          )}
        </div>

        <button
          type="button"
          className="simplify-close-btn"
          onClick={onClose}
          aria-label="Close simplification panel"
        >
          <X size={16} />
        </button>
      </div>

      {/* Controlled demo notice */}
      {controlled_demo && (
        <div className="civic-alert alert-amber simplify-demo-notice">
          <AlertCircle size={15} className="alert-icon" />
          <span>
            <strong>Controlled Demonstration:</strong> This simplification is intentionally incomplete to
            illustrate a Semantic Fidelity failure. It is not a real extraction error.
          </span>
        </div>
      )}

      {/* Simplification quality notice */}
      {qualityNotice && !controlled_demo && (
        <div className={qualityNotice.className}>
          <AlertCircle size={15} className="alert-icon" />
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%", flexWrap: "wrap", gap: "8px" }}>
            <span>{qualityNotice.text}</span>
            {isError && onRetry && (
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={onRetry}
                style={{ padding: "4px 10px", fontSize: "0.8rem", whiteSpace: "nowrap" }}
              >
                Retry Simplification
              </button>
            )}
          </div>
        </div>
      )}

      {/* Translation shortcut if successfully simplified */}
      {!isError && onTranslateSimplified && (
        <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "8px" }}>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => onTranslateSimplified(simplified_text)}
            style={{ fontSize: "0.8rem", display: "inline-flex", alignItems: "center", gap: "6px" }}
          >
            Translate this Simplification in Phase 5 →
          </button>
        </div>
      )}

      {/* Side-by-side comparison */}
      <div className="simplify-comparison">
        <div className="simplify-col">
          <div className="simplify-col-label">Source Passage</div>
          <blockquote className="simplify-source-text">{source_passage}</blockquote>
        </div>
        <div className="simplify-divider" aria-hidden="true" />
        <div className="simplify-col">
          <div className="simplify-col-label">Plain-Language Simplification</div>
          <p className="simplify-output-text">{simplified_text}</p>
        </div>
      </div>

      {/* Reviewer flags — from fidelity (Call 2) only */}
      {fidelity.potentially_missing.length > 0 && (
        <div className="fidelity-flags">
          <div className="fidelity-flags-label">
            <AlertCircle size={14} /> Reviewer flagged possibly missing or altered:
          </div>
          <ul className="fidelity-flags-list">
            {fidelity.potentially_missing.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {fidelity.preserved_conditions.length > 0 && (
        <div className="fidelity-preserved">
          <div className="fidelity-preserved-label">Reviewer confirmed preserved:</div>
          <ul className="fidelity-preserved-list">
            {fidelity.preserved_conditions.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      <p className="simplify-disclaimer">{fidelity.note}</p>
    </div>
  );
}
