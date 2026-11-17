import { useState } from "react";
import { AlertCircle, CheckCircle2, Clock, Globe, Sparkles, X } from "lucide-react";
import CrossLingualBadge from "./CrossLingualBadge";

const API = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

/**
 * BilingualPanel
 *
 * Displays the Phase 5 Cross-Lingual Fidelity result:
 *   - English source passage alongside Hindi Devanagari translation
 *   - Plain-Language Hindi Simplification (सरल हिंदी) with deterministic entity verification
 *   - Input provenance tag (original chunk vs simplified English)
 *   - Two independent assessment rows:
 *       1. Deterministic Term & Number Preservation
 *       2. AI Review Pass (Semantic & Condition Preservation)
 *   - Unified CrossLingualBadge (Preserved only if BOTH checks pass)
 *   - Preserved terms and flagged divergences
 *   - Controlled demo notification when applicable
 */

export default function BilingualPanel({ result, documentId, onClose }) {
  if (!result) return null;

  const {
    chunk_id,
    source_english,
    translated_hindi,
    input_variant,
    term_preservation_status,
    fidelity,
    controlled_demo,
  } = result;

  const [simplifiedHindiData, setSimplifiedHindiData] = useState(null);
  const [isSimplifyingHindi, setIsSimplifyingHindi] = useState(false);
  const [activeHindiView, setActiveHindiView] = useState("formal"); // "formal" | "simplified"

  async function handleSimplifyHindi() {
    if (!documentId || !chunk_id) return;
    setIsSimplifyingHindi(true);
    try {
      const res = await fetch(
        `${API}/api/documents/${documentId}/chunks/${chunk_id}/simplify-hindi`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ hindi_text: translated_hindi }),
        }
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Hindi simplification failed.");
      setSimplifiedHindiData(data);
      setActiveHindiView("simplified");
    } catch (err) {
      console.error("Failed to simplify Hindi:", err);
    } finally {
      setIsSimplifyingHindi(false);
    }
  }

  const termStatusLabels = {
    intact: { label: "Numbers & terms intact", className: "quality-simplified" },
    partial: { label: "Partial entity divergence", className: "quality-insufficient" },
    requires_human_review: { label: "Requires entity review", className: "quality-review" },
  };

  const fidelityStatusLabels = {
    verified: { label: "Meaning & rules preserved", className: "quality-simplified" },
    potential_issue: { label: "Condition or rule divergence", className: "quality-insufficient" },
    requires_human_review: { label: "Requires semantic review", className: "quality-review" },
  };

  const termConfig = termStatusLabels[term_preservation_status] || termStatusLabels.requires_human_review;
  const fidelityConfig = fidelityStatusLabels[fidelity.status] || fidelityStatusLabels.requires_human_review;

  return (
    <div className="bilingual-panel">
      <div className="simplify-panel-header">
        <div className="simplify-panel-title-col">
          <div className="bilingual-title-row">
            <Globe size={16} className="bilingual-header-icon" />
            <span className="simplify-panel-label">Cross-Lingual Fidelity — English / Hindi (हिंदी)</span>
          </div>

          {/* Unified overall status badge */}
          <div className="simplify-assessment-row">
            <span className="simplify-assessment-key">Overall Cross-Lingual Status</span>
            <CrossLingualBadge
              termStatus={term_preservation_status}
              fidelityStatus={fidelity.status}
              controlledDemo={controlled_demo}
            />
          </div>

          {/* Row 1: Deterministic Number & Term Check */}
          <div className="simplify-assessment-row">
            <span className="simplify-assessment-key">Deterministic Term Check</span>
            <span className={`quality-badge ${termConfig.className}`}>
              {termConfig.label}
            </span>
          </div>

          {/* Row 2: Secondary AI Review Pass */}
          <div className="simplify-assessment-row">
            <span className="simplify-assessment-key">AI Review Pass</span>
            <span className={`quality-badge ${fidelityConfig.className}`}>
              {fidelityConfig.label}
            </span>
          </div>

          <div className="input-provenance-tag">
            Input provenance: <strong>{input_variant === "simplified" ? "Simplified English Passage" : "Original Document Chunk"}</strong>
          </div>
        </div>

        <button
          type="button"
          className="simplify-close-btn"
          onClick={onClose}
          aria-label="Close bilingual panel"
        >
          <X size={16} />
        </button>
      </div>

      {/* Controlled demo notice */}
      {controlled_demo && (
        <div className="civic-alert alert-amber simplify-demo-notice">
          <AlertCircle size={15} className="alert-icon" />
          <span>
            <strong>Controlled Demonstration:</strong> A condition or amount was deliberately altered in this
            Hindi translation to demonstrate whether the CDTM cross-lingual evaluation system detects the divergence.
          </span>
        </div>
      )}

      {/* Side-by-side comparison */}
      <div className="simplify-comparison">
        <div className="simplify-col">
          <div className="simplify-col-label">Source English Passage</div>
          <blockquote className="simplify-source-text">{source_english}</blockquote>
        </div>
        <div className="simplify-divider" aria-hidden="true" />
        <div className="simplify-col">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px", flexWrap: "wrap", gap: "6px" }}>
            <div className="simplify-col-label">
              {activeHindiView === "simplified" ? "सरल नागरिक हिंदी (Plain Hindi)" : "मानक हिंदी अनुवाद (Standard Hindi)"}
            </div>
            {simplifiedHindiData ? (
              <div style={{ display: "flex", gap: "6px" }}>
                <button
                  type="button"
                  className={`btn btn-sm ${activeHindiView === "formal" ? "btn-primary" : "btn-secondary"}`}
                  onClick={() => setActiveHindiView("formal")}
                  style={{ padding: "2px 8px", fontSize: "0.75rem" }}
                >
                  मानक हिंदी
                </button>
                <button
                  type="button"
                  className={`btn btn-sm ${activeHindiView === "simplified" ? "btn-primary" : "btn-secondary"}`}
                  onClick={() => setActiveHindiView("simplified")}
                  style={{ padding: "2px 8px", fontSize: "0.75rem" }}
                >
                  सरल हिंदी
                </button>
              </div>
            ) : (
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={handleSimplifyHindi}
                disabled={isSimplifyingHindi}
                style={{ padding: "3px 8px", fontSize: "0.75rem", display: "inline-flex", alignItems: "center", gap: "4px" }}
              >
                <Sparkles size={12} />
                <span>{isSimplifyingHindi ? "सरलीकृत हो रहा है…" : "✨ सरल हिंदी में समझें"}</span>
              </button>
            )}
          </div>

          <p className="simplify-output-text hindi-text">
            {activeHindiView === "simplified" && simplifiedHindiData
              ? simplifiedHindiData.simplified_hindi
              : translated_hindi}
          </p>

          {activeHindiView === "simplified" && simplifiedHindiData && (
            <div style={{ marginTop: "10px", padding: "6px 10px", background: "rgba(34, 197, 94, 0.08)", borderRadius: "6px", border: "1px solid rgba(34, 197, 94, 0.2)", fontSize: "0.78rem", color: "var(--civic-text-primary)", display: "flex", alignItems: "center", gap: "6px" }}>
              <CheckCircle2 size={14} style={{ color: "#16a34a", flexShrink: 0 }} />
              <span>
                <strong>सत्यापित:</strong> सभी तिथियां, आयु सीमा और वित्तीय आंकड़े (₹) सुरक्षित हैं।
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Flagged divergences */}
      {fidelity.potentially_divergent.length > 0 && (
        <div className="fidelity-flags">
          <div className="fidelity-flags-label">
            <AlertCircle size={14} /> Reviewer flagged potential divergence or missing items:
          </div>
          <ul className="fidelity-flags-list">
            {fidelity.potentially_divergent.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Preserved terms */}
      {fidelity.preserved_terms.length > 0 && (
        <div className="fidelity-preserved">
          <div className="fidelity-preserved-label">
            <CheckCircle2 size={14} /> Confirmed preserved terms & entities:
          </div>
          <ul className="fidelity-preserved-list">
            {fidelity.preserved_terms.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      <p className="simplify-disclaimer">{fidelity.note}</p>
    </div>
  );
}
