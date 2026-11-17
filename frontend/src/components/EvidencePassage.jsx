import { useState } from "react";
import { Globe, Sparkles } from "lucide-react";
import SimplifyPanel from "./SimplifyPanel";
import BilingualPanel from "./BilingualPanel";

const API = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function EvidencePassage({
  item,
  isCited,
  isHighlighted,
  filename,
  documentId,
  onTransformation,
}) {
  const [simplifyResult, setSimplifyResult] = useState(null);
  const [simplifyBusy, setSimplifyBusy] = useState(false);
  const [simplifyError, setSimplifyError] = useState("");
  const [showSimplifyPanel, setShowSimplifyPanel] = useState(false);

  const [translateResult, setTranslateResult] = useState(null);
  const [translateBusy, setTranslateBusy] = useState(false);
  const [translateError, setTranslateError] = useState("");
  const [showTranslatePanel, setShowTranslatePanel] = useState(false);

  async function handleSimplify() {
    setSimplifyBusy(true);
    setSimplifyError("");
    try {
      const res = await fetch(
        `${API}/api/documents/${documentId}/chunks/${item.chunk_id}/simplify`,
        { method: "POST" }
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Simplification failed.");
      setSimplifyResult(data);
      setShowSimplifyPanel(true);
      if (onTransformation) {
        onTransformation({ type: "simplify", result: data });
      }
    } catch (err) {
      setSimplifyError(err.message || "Could not reach the simplification endpoint.");
    } finally {
      setSimplifyBusy(false);
    }
  }

  async function handleTranslate() {
    setTranslateBusy(true);
    setTranslateError("");
    try {
      const res = await fetch(
        `${API}/api/documents/${documentId}/chunks/${item.chunk_id}/translate`,
        { method: "POST" }
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Translation failed.");
      setTranslateResult(data);
      setShowTranslatePanel(true);
      if (onTransformation) {
        onTransformation({ type: "translate", result: data });
      }
    } catch (err) {
      setTranslateError(err.message || "Could not reach the translation endpoint.");
    } finally {
      setTranslateBusy(false);
    }
  }

  return (
    <article
      id={`evidence-${item.chunk_id}`}
      className={`evidence-entry${isCited ? " evidence-entry-cited" : ""}${isHighlighted ? " evidence-entry-highlighted" : ""}`}
    >
      <header className="evidence-entry-header">
        <div className="evidence-locators">
          <span className="locator locator-page">Page {item.page_number}</span>
          <span className="locator locator-chunk">{item.chunk_id}</span>
          {isCited && <span className="locator locator-cited-tag">Cited in Answer</span>}
        </div>
        <div className="evidence-score">
          <span className="score-label">BM25 Score</span>
          <span className="score-value">{item.score}</span>
        </div>
      </header>

      <blockquote className="evidence-body">{item.text}</blockquote>

      <footer className="evidence-entry-footer">
        <span className="citation-note">
          Extracted source passage from {filename}, Page {item.page_number}
        </span>
        <div className="evidence-actions">
          <button
            type="button"
            className="btn-simplify"
            onClick={handleSimplify}
            disabled={simplifyBusy}
            title="Simplify this passage and check semantic fidelity"
          >
            <Sparkles size={13} strokeWidth={2} />
            {simplifyBusy ? "Simplifying…" : "Simplify"}
          </button>
          <button
            type="button"
            className="btn-translate"
            onClick={handleTranslate}
            disabled={translateBusy}
            title="Translate this passage to Hindi and check cross-lingual fidelity"
          >
            <Globe size={13} strokeWidth={2} />
            {translateBusy ? "Translating…" : "Translate (हिंदी)"}
          </button>
        </div>
      </footer>

      {simplifyError && <p className="simplify-inline-error">{simplifyError}</p>}
      {translateError && <p className="simplify-inline-error">{translateError}</p>}

      {showSimplifyPanel && simplifyResult && (
        <SimplifyPanel result={simplifyResult} onClose={() => setShowSimplifyPanel(false)} />
      )}
      {showTranslatePanel && translateResult && (
        <BilingualPanel result={translateResult} onClose={() => setShowTranslatePanel(false)} />
      )}
    </article>
  );
}
