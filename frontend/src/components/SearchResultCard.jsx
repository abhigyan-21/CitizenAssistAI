import { useState } from "react";
import { Globe, Sparkles } from "lucide-react";
import SimplifyPanel from "./SimplifyPanel";
import BilingualPanel from "./BilingualPanel";

const API = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function SearchResultCard({ item, documentId, filename, demo = false }) {
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
      const url = `${API}/api/documents/${documentId}/chunks/${item.chunk_id}/simplify${demo ? "?demo=true" : ""}`;
      const res = await fetch(url, { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Simplification failed.");
      setSimplifyResult(data);
      setShowSimplifyPanel(true);
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
      const url = `${API}/api/documents/${documentId}/chunks/${item.chunk_id}/translate${demo ? "?demo=true" : ""}`;
      const res = await fetch(url, { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Translation failed.");
      setTranslateResult(data);
      setShowTranslatePanel(true);
    } catch (err) {
      setTranslateError(err.message || "Could not reach the translation endpoint.");
    } finally {
      setTranslateBusy(false);
    }
  }

  return (
    <article className="evidence-entry">
      <header className="evidence-entry-header">
        <div className="evidence-locators">
          <span className="locator locator-page">Page {item.page_number}</span>
          <span className="locator locator-chunk">{item.chunk_id}</span>
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

      {simplifyError && (
        <p className="simplify-inline-error">{simplifyError}</p>
      )}
      {translateError && (
        <p className="simplify-inline-error">{translateError}</p>
      )}

      {showSimplifyPanel && simplifyResult && (
        <SimplifyPanel result={simplifyResult} onClose={() => setShowSimplifyPanel(false)} />
      )}
      {showTranslatePanel && translateResult && (
        <BilingualPanel result={translateResult} onClose={() => setShowTranslatePanel(false)} />
      )}
    </article>
  );
}
