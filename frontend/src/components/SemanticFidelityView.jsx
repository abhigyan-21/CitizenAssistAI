import { useState } from "react";
import { Sparkles, AlertCircle, ChevronDown, ChevronUp, FileText } from "lucide-react";
import SimplifyPanel from "./SimplifyPanel";

const API = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function SemanticFidelityView({
  documentId,
  chunks = [],
  selectedChunkId,
  onSelectChunkId,
  qaResult,
  simplificationResult,
  onSimplificationComplete,
  onNavigateToTranslation,
  demoMode = false,
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);

  // Active chunk
  const activeChunk = chunks.find((c) => c.chunk_id === selectedChunkId) || chunks[0];
  const isCited = qaResult?.cited_chunk_ids?.includes(activeChunk?.chunk_id);

  async function handleSimplify() {
    if (!activeChunk || !documentId) return;
    setBusy(true);
    setError("");

    try {
      const url = `${API}/api/documents/${documentId}/chunks/${activeChunk.chunk_id}/simplify${
        demoMode ? "?demo=true" : ""
      }`;
      const res = await fetch(url, { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Simplification request failed.");
      onSimplificationComplete(data);
    } catch (err) {
      setError(err.message || "Could not connect to simplification service.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="phase-workbench-shell">
      {/* Chunk Selector */}
      <div className="chunk-selector-card">
        <div className="chunk-selector-top">
          <label htmlFor="chunk-select" className="chunk-selector-label">
            <FileText size={14} /> Select Document Passage to Simplify:
          </label>
          {isCited && (
            <span className="badge-cited-qa">Cited Evidence in Q&amp;A</span>
          )}
        </div>

        <div className="chunk-selector-controls">
          <select
            id="chunk-select"
            className="chunk-dropdown"
            value={activeChunk?.chunk_id || ""}
            onChange={(e) => onSelectChunkId(e.target.value)}
            disabled={busy}
          >
            {chunks.map((c) => {
              const cited = qaResult?.cited_chunk_ids?.includes(c.chunk_id);
              const preview = c.text?.slice(0, 60).replace(/\s+/g, " ") || "";
              return (
                <option key={c.chunk_id} value={c.chunk_id}>
                  {c.chunk_id} (Page {c.page_number}){cited ? " ★ Cited" : ""} — "{preview}…"
                </option>
              );
            })}
          </select>

          <button
            type="button"
            className="btn btn-primary btn-action-simplify"
            onClick={handleSimplify}
            disabled={busy || !activeChunk}
          >
            <Sparkles size={14} />
            <span>{busy ? "Auditing Semantic Fidelity…" : "Simplify Passage"}</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="civic-alert alert-error">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Side-by-Side Source vs Transformation */}
      <div className="workbench-dual-grid">
        {/* Source Column */}
        <div className="workbench-column source-col">
          <header className="wb-col-header">
            <span className="wb-col-tag">OFFICIAL SOURCE CLAUSE</span>
            <span className="wb-col-meta">
              Chunk: {activeChunk?.chunk_id || "None"} · Page {activeChunk?.page_number || "1"}
            </span>
          </header>
          <div className="wb-col-body">
            <p className="source-passage-text">
              {activeChunk?.text || "No passage selected."}
            </p>
          </div>
        </div>

        {/* Output Column */}
        <div className="workbench-column result-col">
          <header className="wb-col-header">
            <span className="wb-col-tag">PLAIN-LANGUAGE TRANSFORMATION</span>
            <span className="wb-col-meta">Two-Call AI Fidelity Review</span>
          </header>
          <div className="wb-col-body">
            {simplificationResult && simplificationResult.chunk_id === activeChunk?.chunk_id ? (
              <SimplifyPanel
                result={simplificationResult}
                onClose={() => onSimplificationComplete(null)}
                onRetry={handleSimplify}
                onTranslateSimplified={onNavigateToTranslation}
              />
            ) : busy ? (
              <div className="workbench-loading-state">
                <span className="loading-spinner"></span>
                <p>Call 1: Generating plain-language plain rewrite…</p>
                <p className="loading-sub">Call 2: Evaluating condition and exclusion preservation…</p>
              </div>
            ) : (
              <div className="workbench-empty-state">
                <p>Click <strong>"Simplify Passage"</strong> above to generate a plain-language explanation and execute the semantic fidelity review.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Collapsible Technical Details */}
      <div className="workbench-collapsible-section">
        <button
          type="button"
          className="btn-toggle-collapsible"
          onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
        >
          <span>Technical Architecture: Two-Call Fidelity Reviewer</span>
          {showTechnicalDetails ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
        </button>

        {showTechnicalDetails && (
          <div className="collapsible-drawer-content">
            <p>
              <strong>Evaluation Protocol:</strong> Plain-language simplification employs a decoupled two-call architecture:
            </p>
            <ul className="drawer-bullets">
              <li>
                <strong>Call 1 (Simplification):</strong> Rewrites bureaucratic legal phrasing into straightforward citizen English without adding outside facts.
              </li>
              <li>
                <strong>Call 2 (Fidelity Auditor):</strong> A separate evaluation call inspects whether the simplified version dropped statutory eligibility criteria, reversed negations, changed exclusion clauses, or mutated monetary amounts.
              </li>
              <li>
                <strong>Deterministic Quality Check:</strong> A SequenceMatcher baseline calculates string similarity to guarantee that actual simplification occurred rather than an verbatim echo.
              </li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
