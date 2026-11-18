import { useState } from "react";
import { Globe, AlertCircle, ChevronDown, ChevronUp, FileText, Sparkles } from "lucide-react";
import BilingualPanel from "./BilingualPanel";

const API = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function CrossLingualView({
  documentId,
  chunks = [],
  selectedChunkId,
  onSelectChunkId,
  qaResult,
  translationResult,
  onTranslationComplete,
  simplificationResult,
  onNavigateToSimplification,
  demoMode = false,
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
  const [translateVariant, setTranslateVariant] = useState("original"); // "original" | "simplified"

  const activeChunk = chunks.find((c) => c.chunk_id === selectedChunkId) || chunks[0];
  const isCited = qaResult?.cited_chunk_ids?.includes(activeChunk?.chunk_id);
  const hasValidSimplification =
    simplificationResult &&
    simplificationResult.chunk_id === activeChunk?.chunk_id &&
    simplificationResult.simplification_quality !== "error";

  async function handleTranslate() {
    if (!activeChunk || !documentId) return;
    setBusy(true);
    setError("");

    const isSimplified = translateVariant === "simplified" && hasValidSimplification;
    let url = `${API}/api/documents/${documentId}/chunks/${activeChunk.chunk_id}/translate?target_language=hi${
      isSimplified ? "&input_variant=simplified" : ""
    }`;
    if (demoMode) {
      url += "&demo=true";
    }
    const options = {
      method: "POST",
      headers: isSimplified ? { "Content-Type": "application/json" } : {},
      body: isSimplified
        ? JSON.stringify({ simplified_text: simplificationResult.simplified_text })
        : undefined,
    };

    try {
      const res = await fetch(url, options);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Translation request failed.");
      onTranslationComplete(data);
    } catch (err) {
      setError(err.message || "Could not connect to translation service.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="phase-workbench-shell">
      {/* Chunk Selector */}
      <div className="chunk-selector-card">
        <div className="chunk-selector-top">
          <label htmlFor="chunk-select-trans" className="chunk-selector-label">
            <FileText size={14} /> Select Document Passage to Translate:
          </label>
          <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
            {isCited && (
              <span className="badge-cited-qa">Cited Evidence in Q&amp;A</span>
            )}
            {onNavigateToSimplification && (
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={onNavigateToSimplification}
                style={{ fontSize: "0.78rem", padding: "2px 8px", display: "inline-flex", alignItems: "center", gap: "4px" }}
              >
                <Sparkles size={12} />
                <span>{hasValidSimplification ? "View Simplification" : "Simplify Passage First"}</span>
              </button>
            )}
          </div>
        </div>

        <div className="chunk-selector-controls">
          <select
            id="chunk-select-trans"
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
            className="btn btn-primary btn-action-translate"
            onClick={handleTranslate}
            disabled={busy || !activeChunk}
          >
            <Globe size={14} />
            <span>
              {busy
                ? "Auditing Cross-Lingual Fidelity…"
                : translateVariant === "simplified" && hasValidSimplification
                ? "Translate Simplified to Hindi"
                : "Translate to Hindi (हिंदी)"}
            </span>
          </button>
        </div>

        {/* Input Variant Selector (Original vs Simplified) */}
        {hasValidSimplification && (
          <div style={{ marginTop: "12px", display: "flex", alignItems: "center", gap: "10px", fontSize: "0.85rem" }}>
            <span style={{ fontWeight: 600, color: "var(--civic-text-secondary)" }}>Input Source:</span>
            <button
              type="button"
              className={`btn btn-sm ${translateVariant === "original" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setTranslateVariant("original")}
              style={{ fontSize: "0.8rem", padding: "3px 10px" }}
            >
              Original Legal Text
            </button>
            <button
              type="button"
              className={`btn btn-sm ${translateVariant === "simplified" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setTranslateVariant("simplified")}
              style={{ fontSize: "0.8rem", padding: "3px 10px" }}
            >
              Plain-Language Simplification (Phase 4)
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="civic-alert alert-error">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Side-by-Side Source vs Transformation */}
      <div className="workbench-dual-grid">
        {/* Source English Column */}
        <div className="workbench-column source-col">
          <header className="wb-col-header">
            <span className="wb-col-tag">
              {translateVariant === "simplified" && hasValidSimplification
                ? "PLAIN-LANGUAGE ENGLISH (PHASE 4)"
                : "ENGLISH SOURCE PASSAGE"}
            </span>
            <span className="wb-col-meta">
              Chunk: {activeChunk?.chunk_id || "None"} · Page {activeChunk?.page_number || "1"}
            </span>
          </header>
          <div className="wb-col-body">
            <p className="source-passage-text">
              {translateVariant === "simplified" && hasValidSimplification
                ? simplificationResult.simplified_text
                : activeChunk?.text || "No passage selected."}
            </p>
          </div>
        </div>

        {/* Output Hindi Column */}
        <div className="workbench-column result-col">
          <header className="wb-col-header">
            <span className="wb-col-tag">HINDI DEVANAGARI TRANSLATION</span>
            <span className="wb-col-meta">Deterministic &amp; AI Audit</span>
          </header>
          <div className="wb-col-body">
            {translationResult && translationResult.chunk_id === activeChunk?.chunk_id ? (
              <BilingualPanel
                result={translationResult}
                documentId={documentId}
                onClose={() => onTranslationComplete(null)}
                demoMode={demoMode}
              />
            ) : busy ? (
              <div className="workbench-loading-state">
                <span className="loading-spinner"></span>
                <p>Translating administrative terminology to Hindi…</p>
                <p className="loading-sub">Running deterministic numeral checks and Call 2 reviewer…</p>
              </div>
            ) : (
              <div className="workbench-empty-state">
                <p>Click <strong>"Translate to Hindi"</strong> above to generate a Devanagari translation and audit statutory terminology consistency.</p>
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
          <span>Technical Architecture: Deterministic Entities &amp; Bilingual Reviewer</span>
          {showTechnicalDetails ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
        </button>

        {showTechnicalDetails && (
          <div className="collapsible-drawer-content">
            <p>
              <strong>Cross-Lingual Verification Protocol:</strong>
            </p>
            <ul className="drawer-bullets">
              <li>
                <strong>Step 1 (Deterministic Entity Extraction):</strong> Normalizes Hindu-Arabic and Devanagari numerals, currency symbols (₹, Rs), and statutory keywords to ensure numbers and deadlines match exactly.
              </li>
              <li>
                <strong>Step 2 (Semantic Review Pass):</strong> An independent review pass inspects whether government benefit rules, exclusion definitions, or statutory conditions drifted in translation.
              </li>
              <li>
                <strong>Decoupled Verdict:</strong> Term preservation and semantic fidelity remain separate assessment tracks. A translation is only marked preserved when both tiers pass.
              </li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
