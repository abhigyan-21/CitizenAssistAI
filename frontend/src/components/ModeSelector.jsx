import { Bot, ShieldAlert, Sparkles, CheckCircle2 } from "lucide-react";

export default function ModeSelector({ mode, onSelectMode }) {
  return (
    <div className="mode-selector-wrapper">
      <div className="mode-selector-header">
        <span className="mode-selector-tag">RESEARCH DEMONSTRATION MODE</span>
        <h3 className="mode-selector-title">Assistance Paradigm Comparison</h3>
      </div>

      <div className="mode-selector-toggle-group" role="tablist" aria-label="Assistance Mode">
        <button
          type="button"
          role="tab"
          aria-selected={mode === "basic"}
          className={`mode-btn ${mode === "basic" ? "mode-btn-active mode-basic" : ""}`}
          onClick={() => onSelectMode("basic")}
        >
          <div className="mode-btn-icon">
            <Bot size={18} />
          </div>
          <div className="mode-btn-text">
            <div className="mode-btn-heading">
              <strong>Basic AI Assistance</strong>
              <span className="mode-type-tag tag-unverified">Unverified Baseline</span>
            </div>
            <p className="mode-btn-desc">
              Unverified baseline generation using the same retrieved source context. No citation
              checks, claim auditing, or CDTM fidelity evaluation.
            </p>
          </div>
          {mode === "basic" && <CheckCircle2 size={16} className="mode-selected-check" />}
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={mode === "cdtm"}
          className={`mode-btn ${mode === "cdtm" ? "mode-btn-active mode-cdtm" : ""}`}
          onClick={() => onSelectMode("cdtm")}
        >
          <div className="mode-btn-icon">
            <Sparkles size={18} />
          </div>
          <div className="mode-btn-text">
            <div className="mode-btn-heading">
              <strong>CDTM-Guided Assistance</strong>
              <span className="mode-type-tag tag-guided">Governed Framework</span>
            </div>
            <p className="mode-btn-desc">
              Claim-level evidence grounding, verified citations, plain-language fidelity, and
              multi-dimensional CDTM audit.
            </p>
          </div>
          {mode === "cdtm" && <CheckCircle2 size={16} className="mode-selected-check" />}
        </button>
      </div>
    </div>
  );
}
