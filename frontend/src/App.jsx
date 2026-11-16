import { useState } from "react";
import {
  FileUp,
  FileText,
  Search,
  AlertCircle,
  CheckCircle2,
  BookOpen,
} from "lucide-react";

const API = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  // BM25 Retrieval states
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState(null);
  const [searchBusy, setSearchBusy] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [hasSearched, setHasSearched] = useState(false);

  function resetSearch() {
    setQuery("");
    setSearchResults(null);
    setSearchError("");
    setHasSearched(false);
  }

  async function extract(event) {
    event.preventDefault();
    if (!file) return setError("Select a PDF document first.");
    setBusy(true);
    setError("");
    setResult(null);
    resetSearch();

    const body = new FormData();
    body.append("file", file);

    try {
      const response = await fetch(`${API}/api/documents/extract`, {
        method: "POST",
        body,
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Extraction failed.");
      setResult(data);
    } catch (err) {
      setError(err.message || "Could not connect to the backend.");
    } finally {
      setBusy(false);
    }
  }

  async function handleSearch(event) {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) {
      setSearchError("Please enter a question or query term.");
      return;
    }
    if (!result?.document_id) {
      setSearchError("Please upload and extract a document first.");
      return;
    }

    setSearchBusy(true);
    setSearchError("");

    try {
      const response = await fetch(`${API}/api/documents/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          document_id: result.document_id,
          query: trimmed,
          top_k: 5,
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Search failed.");
      setSearchResults(data);
      setHasSearched(true);
    } catch (err) {
      setSearchError(err.message || "Could not connect to the search endpoint.");
    } finally {
      setSearchBusy(false);
    }
  }

  return (
    <div className="app-canvas">
      {/* Editorial Masthead */}
      <header className="masthead">
        <div className="masthead-inner">
          <div className="masthead-brand">
            <span className="brand-mark">
              <BookOpen size={18} strokeWidth={2} />
            </span>
            <div className="brand-titles">
              <span className="brand-title">CitizenAssist AI</span>
              <span className="brand-subtitle">
                Multilingual Administrative Document Assistance · नागरिक दस्तावेज़ सहायता
              </span>
            </div>
          </div>
          <div className="masthead-meta">
            <span className="meta-tag">Research Demonstrator</span>
            <span className="meta-divider">|</span>
            <span className="meta-tag">CDTM-Guided</span>
          </div>
        </div>
      </header>

      <main className="content-shell">
        {/* Editorial Lead Section */}
        <section className="lead-section">
          <div className="lead-eyebrow">ADMINISTRATIVE SCHEME & GUIDELINE ANALYSIS</div>
          <h1 className="lead-headline">
            Uploaded administrative documents, structured for clarity and evidentiary inspection.
          </h1>
          <p className="lead-description">
            Upload public operational guidelines, gazettes, or scheme manuals. This research system
            extracts page-isolated text, builds lexical indexes, and retrieves source passages to
            ground citizen inquiries in traceable source-document evidence.
          </p>
        </section>

        {/* STEP 01: Document Intake */}
        <section className="civic-card intake-card">
          <div className="card-header">
            <div>
              <span className="card-step">PHASE 01</span>
              <h2 className="card-title">Document Intake</h2>
            </div>
            <span className="status-label">PDF Extraction</span>
          </div>

          <form onSubmit={extract} className="intake-form">
            <label className="intake-dropzone">
              <input
                type="file"
                accept="application/pdf,.pdf"
                onChange={(e) => {
                  setFile(e.target.files?.[0] || null);
                  setResult(null);
                  setError("");
                  resetSearch();
                }}
              />
              <span className="dropzone-icon">
                <FileUp size={24} strokeWidth={1.8} />
              </span>
              <div className="dropzone-text">
                <strong className="dropzone-file-name">
                  {file ? file.name : "Select an administrative PDF document"}
                </strong>
                <span className="dropzone-hint">
                  {file
                    ? `${(file.size / 1048576).toFixed(2)} MB · Ready for processing`
                    : "Standard PDF format · Maximum upload limit 20 MB"}
                </span>
              </div>
              <span className="dropzone-action">Browse filesystem</span>
            </label>

            {error && (
              <div className="civic-alert alert-error">
                <AlertCircle size={16} className="alert-icon" />
                <span>{error}</span>
              </div>
            )}

            <div className="form-actions">
              <button
                type="submit"
                className="btn btn-primary"
                disabled={!file || busy}
              >
                {busy
                  ? "Extracting Document..."
                  : file
                  ? "Extract Document Text"
                  : "Select a PDF to enable"}
              </button>
            </div>
          </form>
        </section>

        {/* Extracted Document Workspace */}
        {result && (
          <section className="civic-card workspace-card">
            {/* Document Summary Docket */}
            <div className="docket-header">
              <div className="docket-identity">
                <div className="docket-icon">
                  <FileText size={20} strokeWidth={1.8} />
                </div>
                <div>
                  <h3 className="docket-filename">{result.filename}</h3>
                  <div className="docket-specs">
                    <span>{result.page_count} page(s) extracted</span>
                    <span className="specs-sep">•</span>
                    <span>{result.chunk_count} text partitions</span>
                    <span className="specs-sep">•</span>
                    <span className="specs-hash">ID: {result.document_id}</span>
                  </div>
                </div>
              </div>

              <div className="docket-status-group">
                <span className="status-pill status-extracted">
                  <CheckCircle2 size={13} strokeWidth={2} />
                  Document Successfully Extracted
                </span>
              </div>
            </div>

            {/* Warnings (Amber strictly) */}
            {result.warnings && result.warnings.length > 0 && (
              <div className="civic-alert alert-amber">
                <AlertCircle size={16} className="alert-icon" />
                <div className="alert-content">
                  <strong className="alert-title">Document Extraction Notice</strong>
                  {result.warnings.map((w, idx) => (
                    <p key={idx} className="alert-message">{w}</p>
                  ))}
                </div>
              </div>
            )}

            {/* Source Fidelity Advisory */}
            <div className="fidelity-advisory">
              <div className="advisory-title">
                <BookOpen size={14} />
                <span>Source Fidelity Status: <strong>{result.source_fidelity_status}</strong></span>
              </div>
              <p className="advisory-text">
                Extraction completed for selectable text layers. Full factual fidelity evaluation and
                cross-verification against legal amendments is performed in later CDTM evaluation stages.
              </p>
            </div>

            {/* STEP 02: BM25 Document Search */}
            <div className="search-section">
              <div className="card-header section-subhead">
                <div>
                  <span className="card-step">PHASE 02</span>
                  <h2 className="card-title">Document Evidence Retrieval</h2>
                </div>
                <span className="status-label">BM25 Lexical Ranking</span>
              </div>

              {/* Explicit Grounding Notice */}
              <div className="grounding-notice">
                <p>
                  <strong>Notice on Retrieved Evidence:</strong> Direct textual retrieval from the uploaded administrative document via BM25. <em>These are retrieved source passages, not AI-generated answers.</em>
                </p>
              </div>

              <form onSubmit={handleSearch} className="search-form">
                <div className="search-input-group">
                  <Search size={18} className="search-icon" />
                  <input
                    type="text"
                    className="search-field"
                    placeholder="Enter query terms or scheme provisions (e.g., eligibility criteria, exclusion, landholder, DBT)..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    disabled={searchBusy}
                  />
                  <button
                    type="submit"
                    className="btn btn-secondary"
                    disabled={searchBusy || !query.trim()}
                  >
                    {searchBusy ? "Searching…" : "Retrieve Passages"}
                  </button>
                </div>
              </form>

              {searchError && (
                <div className="civic-alert alert-error">
                  <AlertCircle size={16} className="alert-icon" />
                  <span>{searchError}</span>
                </div>
              )}

              {searchBusy && (
                <div className="state-notice loading-state">
                  <span>Searching document chunks with BM25 lexical index…</span>
                </div>
              )}

              {hasSearched && !searchBusy && searchResults && (
                <div className="evidence-results-container">
                  {searchResults.results.length === 0 ? (
                    <div className="state-notice no-results-state">
                      <AlertCircle size={16} />
                      <span>
                        No matching passages found for query <em>"{searchResults.query}"</em>. Try
                        alternative keywords or statutory terminology.
                      </span>
                    </div>
                  ) : (
                    <div className="evidence-list">
                      <div className="evidence-header-bar">
                        <span className="evidence-count">
                          Retrieved Source Evidence: <strong>{searchResults.results.length} passage(s)</strong>
                        </span>
                        <span className="evidence-criterion">
                          Top-5 BM25 relevance scores
                        </span>
                      </div>

                      {searchResults.results.map((item) => (
                        <article className="evidence-entry" key={item.chunk_id}>
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

                          <blockquote className="evidence-body">
                            {item.text}
                          </blockquote>

                          <footer className="evidence-entry-footer">
                            <span className="citation-note">
                              Extracted source passage from {result.filename}, Page {item.page_number}
                            </span>
                          </footer>
                        </article>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Extracted Page-by-Page Text (Linear presentation preserved) */}
            <div className="extracted-section">
              <div className="card-header section-subhead">
                <div>
                  <span className="card-step">RECORD ARCHIVE</span>
                  <h2 className="card-title">Extracted Document Text</h2>
                </div>
                <span className="status-label">Sequential Page View</span>
              </div>

              <div className="pages-stream">
                {result.pages.map((page) => (
                  <article className="page-folio" key={page.page_number}>
                    <div className="folio-header">
                      <span className="folio-number">PAGE {String(page.page_number).padStart(2, "0")}</span>
                      <span className="folio-meta">
                        {page.text ? `${page.text.length} characters` : "No text content"}
                      </span>
                    </div>
                    <div className="folio-body">
                      {page.text ? (
                        <p className="folio-text">{page.text}</p>
                      ) : (
                        <p className="folio-empty">
                          No selectable text found on this page. Optical character recognition (OCR) will be
                          applied in subsequent milestones.
                        </p>
                      )}
                    </div>
                  </article>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* CDTM Trustworthiness Evaluation Pipeline Section */}
        <section className="civic-card pipeline-card">
          <div className="card-header">
            <div>
              <span className="card-step">EVALUATION FRAMEWORK</span>
              <h2 className="card-title">CDTM Trustworthiness Evaluation</h2>
            </div>
            <span className="status-label">Five Trustworthiness Dimensions</span>
          </div>

          <p className="pipeline-lead">
            The Citizen Document Trustworthiness Model (CDTM) evaluates automated assistance systems
            against five critical dimensions to prevent bureaucratic hallucinations and procedural errors.
          </p>

          <div className="cdtm-grid">
            <DimensionCard
              number="01"
              title="Source Fidelity"
              status="Extracting & Grounding Active"
              statusType="active"
              detail="Verifies that all extracted statements and retrieved passages correspond strictly to verified clauses in the official source document without extrapolation."
            />
            <DimensionCard
              number="02"
              title="Exclusion & Rule Completeness"
              status="Planned Milestone"
              statusType="planned"
              detail="Inspects answers for critical administrative exclusions, mandatory criteria, statutory cut-offs, and landholding qualifications to avoid false eligibility claims."
            />
            <DimensionCard
              number="03"
              title="Plain-Language Clarity"
              status="Planned Milestone"
              statusType="planned"
              detail="Measures readability and structural simplification, transforming convoluted administrative terminology into plain, comprehensible English."
            />
            <DimensionCard
              number="04"
              title="Cross-Lingual Preservation"
              status="Planned Milestone"
              statusType="planned"
              detail="Evaluates semantic and numeric consistency in Hindi translations, verifying that statutory dates, monetary benefits, and official terms remain intact."
            />
            <DimensionCard
              number="05"
              title="Procedural Actionability"
              status="Planned Milestone"
              statusType="planned"
              detail="Audits institutional action pathways (application portals, verification authorities, nodal officers) to prevent misdirection of citizen applicants."
            />
          </div>
        </section>
      </main>

      {/* Editorial Colophon / Footer */}
      <footer className="colophon">
        <div className="colophon-inner">
          <div className="colophon-main">
            <span className="colophon-title">CitizenAssist AI</span>
            <p className="colophon-text">
              An open-source research demonstrator for administrative document simplification and evidentiary grounding.
              Outputs must always be cross-referenced with official central or state government portals.
            </p>
          </div>
          <div className="colophon-meta">
            <span>Reference Document: PM-KISAN Operational Guidelines</span>
            <span>Non-Governmental Academic & Engineering Demonstrator</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

function DimensionCard({ number, title, status, statusType, detail }) {
  return (
    <article className="dimension-card">
      <div className="dimension-header">
        <span className="dimension-number">{number}</span>
        <span className={`status-pill ${statusType === "active" ? "status-active" : "status-planned"}`}>
          {status}
        </span>
      </div>
      <h3 className="dimension-title">{title}</h3>
      <p className="dimension-detail">{detail}</p>
    </article>
  );
}
