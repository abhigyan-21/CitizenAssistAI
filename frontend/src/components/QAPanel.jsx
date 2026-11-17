import { useState } from "react";
import { Search, AlertCircle, Sparkles, ChevronDown, ChevronUp, Bot, GitCompare, Shield } from "lucide-react";
import CitationBadge from "./CitationBadge";
import EvidencePassage from "./EvidencePassage";

export default function QAPanel({
  mode = "cdtm",
  askQuery,
  onAskQueryChange,
  onAsk,
  qaBusy,
  qaError,
  hasAsked,
  qaResult,
  highlightedChunkId,
  onScrollToEvidence,
  filename,
  documentId,
  onOpenComparison,
}) {
  const [showEvidence, setShowEvidence] = useState(true);

  const isBasic = mode === "basic";

  return (
    <div className={`qa-section ${isBasic ? "qa-section-basic" : "qa-section-cdtm"}`}>
      <div className="card-header section-subhead">
        <div>
          <span className="card-step">
            {isBasic ? "BASELINE ASSISTANCE" : "PHASE 03 · GROUNDED ASSISTANCE"}
          </span>
          <h2 className="card-title">
            {isBasic ? "Basic AI Generative Assistance" : "AI-Assisted Document Understanding"}
          </h2>
        </div>
        <div className="header-badges-row">
          {isBasic ? (
            <span className="status-label status-basic">
              <Bot size={13} />
              Basic Generative (Unverified)
            </span>
          ) : (
            <span className="status-label status-gemini">
              <Sparkles size={13} />
              Evidence-Grounded Q&amp;A
            </span>
          )}

          {hasAsked && onOpenComparison && (
            <button
              type="button"
              className="btn btn-compare-pill"
              onClick={onOpenComparison}
            >
              <GitCompare size={13} />
              <span>Comparative Audit</span>
            </button>
          )}
        </div>
      </div>

      {/* Mode-specific disclaimer */}
      {isBasic ? (
        <div className="civic-alert alert-basic-disclaimer">
          <AlertCircle size={18} className="alert-icon" />
          <div className="alert-content">
            <strong className="alert-title">Basic Mode — Unverified Baseline Generation</strong>
            <p className="alert-text">
              Basic Mode: Unverified baseline generation using the same retrieved source context.
              Claims are not subject to enforced citation validation, claim-level evidence auditing
              or CDTM fidelity evaluation.
            </p>
          </div>
        </div>
      ) : (
        <div className="grounding-notice ai-grounding-notice">
          <p>
            <strong>Evidentiary Grounding Protocol:</strong> Answers are formulated exclusively from the
            top retrieved passages of this document. If the document does not contain verifiable facts to
            answer, the model is instructed to explicitly abstain.
          </p>
        </div>
      )}

      <form onSubmit={onAsk} className="qa-form">
        <div className="search-input-group qa-input-group">
          <Search size={18} className="search-icon" />
          <input
            type="text"
            className="search-field"
            placeholder={
              isBasic
                ? "Ask a question (standard generative generation without citation auditing)..."
                : "Ask a natural-language question (e.g., What is the definition of a beneficiary family?)..."
            }
            value={askQuery}
            onChange={(e) => onAskQueryChange(e.target.value)}
            disabled={qaBusy}
          />
          <button
            type="submit"
            className={`btn ${isBasic ? "btn-ask-basic" : "btn-ask"}`}
            disabled={qaBusy || !askQuery.trim()}
          >
            {qaBusy ? "Generating Response…" : isBasic ? "Ask (Basic Mode)" : "Ask Document"}
          </button>
        </div>
      </form>

      {qaError && (
        <div className="civic-alert alert-error">
          <AlertCircle size={16} className="alert-icon" />
          <span>{qaError}</span>
        </div>
      )}

      {qaBusy && (
        <div className="state-notice loading-state">
          <span>
            {isBasic
              ? "Generating standard baseline generative answer…"
              : "Consulting document passages and formulating evidence-grounded answer…"}
          </span>
        </div>
      )}

      {hasAsked && !qaBusy && qaResult && (
        <div className="qa-response-container">
          {/* Abstention Card (only applicable when insufficient_evidence is flagged) */}
          {qaResult.insufficient_evidence ? (
            <div className="civic-alert alert-amber abstention-card">
              <AlertCircle size={18} className="alert-icon" />
              <div className="alert-content">
                <strong className="alert-title">Insufficient Evidence in Document</strong>
                <p className="abstention-text">{qaResult.answer}</p>
                <span className="abstention-hint">
                  The system abstained because the uploaded text partitions do not contain verifiable
                  statements to answer this question without speculation.
                </span>
              </div>
            </div>
          ) : isBasic ? (
            /* BASIC MODE: Plain generative answer card without citation pills or evidence drawer */
            <article className="grounded-answer-card basic-answer-card">
              <header className="answer-header basic-header">
                <div className="answer-title-group">
                  <span className="answer-badge badge-basic">
                    <Bot size={13} /> Basic AI Answer
                  </span>
                  <span className="model-tag">
                    Model: {qaResult.provider_info?.model || "AI"}
                  </span>
                </div>
                <span className="disclaimer-chip unverified-chip">Uninspected Citations</span>
              </header>

              <div className="answer-body">
                <p className="answer-text">{qaResult.answer}</p>
              </div>

              <footer className="basic-answer-footer">
                <span className="basic-audit-hint">
                  Notice: Chunk-level citations and claim grounding checks are not performed in Basic Mode.
                </span>
                {onOpenComparison && (
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={onOpenComparison}
                  >
                    <GitCompare size={14} /> Compare with CDTM-Guided Mode
                  </button>
                )}
              </footer>
            </article>
          ) : (
            /* CDTM-GUIDED MODE: Full grounded answer card with citation pills & evidence drawer */
            <article className="grounded-answer-card">
              <header className="answer-header">
                <div className="answer-title-group">
                  <span className="answer-badge">
                    <Sparkles size={13} /> Grounded Answer
                  </span>
                  <span className="model-tag">
                    Model: {qaResult.provider_info?.model || "AI"}
                  </span>
                </div>
                <span className="disclaimer-chip">Subject to source citations</span>
              </header>

              <div className="answer-body">
                <p className="answer-text">{qaResult.answer}</p>
              </div>

              {qaResult.citations?.length > 0 && (
                <div className="citations-tray">
                  <span className="citations-tray-label">Source Document Citations:</span>
                  <div className="citation-pills-list">
                    {qaResult.citations.map((cite) => (
                      <CitationBadge
                        key={cite.chunk_id}
                        citation={cite}
                        isActive={highlightedChunkId === cite.chunk_id}
                        onClick={onScrollToEvidence}
                      />
                    ))}
                  </div>
                </div>
              )}
            </article>
          )}

          {/* Supporting Evidence Drawer (CDTM-Guided mode only) */}
          {!isBasic && qaResult.retrieved_evidence?.length > 0 && (
            <div className="supporting-evidence-section">
              <button
                type="button"
                className="btn-toggle-evidence"
                onClick={() => setShowEvidence((v) => !v)}
              >
                <span>
                  {showEvidence ? "Hide Supporting Evidence Passages" : "Inspect Supporting Evidence Passages"}
                  {" "}({qaResult.retrieved_evidence.length} retrieved chunks)
                </span>
                {showEvidence ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </button>

              {showEvidence && (
                <div className="evidence-passages-drawer">
                  {qaResult.retrieved_evidence.map((item) => (
                    <EvidencePassage
                      key={item.chunk_id}
                      item={item}
                      isCited={qaResult.cited_chunk_ids?.includes(item.chunk_id)}
                      isHighlighted={highlightedChunkId === item.chunk_id}
                      filename={filename}
                      documentId={documentId}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
