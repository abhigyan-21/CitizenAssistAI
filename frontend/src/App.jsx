import { useState } from "react";
import { FileUp, FileText, ShieldCheck, Languages, Search, AlertCircle, CheckCircle2 } from "lucide-react";

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
    if (!file) return setError("Choose a PDF first.");
    setBusy(true);
    setError("");
    setResult(null);
    resetSearch();

    const body = new FormData();
    body.append("file", file);

    try {
      const response = await fetch(`${API}/api/documents/extract`, { method: "POST", body });
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
      setSearchError("Please enter a question or keyword to search.");
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
    <main className="shell">
      <header className="topbar">
        <a className="brand" href="#">
          <span className="brandmark"><ShieldCheck size={20} /></span>
          CitizenAssist <b>AI</b>
        </a>
        <span className="muted">Research demonstrator · CDTM-guided</span>
      </header>

      <section className="hero">
        <div className="eyebrow">ADMINISTRATIVE DOCUMENT UNDERSTANDING</div>
        <h1>
          Government information,<br />
          <span>made easier to understand.</span>
        </h1>
        <p>
          Upload an administrative document to begin. This milestone extracts page-level text and supports BM25 evidence retrieval; simplification, Hindi translation, generative AI answers and CDTM evaluation will follow.
        </p>
      </section>

      <section className="panel">
        <div className="sectionhead">
          <div>
            <div className="eyebrow">STEP 01</div>
            <h2>Upload a document</h2>
          </div>
          <span className="pill">PDF extraction</span>
        </div>
        <form onSubmit={extract}>
          <label className="dropzone">
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
            <span className="uploadicon"><FileUp size={25} /></span>
            <strong>{file ? file.name : "Choose a PDF document"}</strong>
            <span className="muted">
              {file ? `${(file.size / 1048576).toFixed(2)} MB` : "PDF format · Maximum 20 MB"}
            </span>
            <span className="link">Browse files</span>
          </label>
          {error && <div className="alert error"><AlertCircle size={17} />{error}</div>}
          <button className="primary" disabled={!file || busy}>
            {busy ? "Extracting…" : "Extract document text"}
          </button>
        </form>
      </section>

      {result && (
        <section className="panel result">
          <div className="resulthead">
            <div className="filetitle">
              <span className="fileicon"><FileText /></span>
              <div>
                <b>{result.filename}</b>
                <div className="muted">{result.page_count} page(s) processed · Doc ID: {result.document_id}</div>
              </div>
            </div>
            <span className="success"><CheckCircle2 size={15} /> Extraction complete</span>
          </div>

          {result.warnings.length > 0 && (
            <div className="alert warning">
              <AlertCircle size={17} />
              <div>{result.warnings.map((w) => <p key={w}>{w}</p>)}</div>
            </div>
          )}

          {/* STEP 02: BM25 EVIDENCE RETRIEVAL */}
          <div className="search-section">
            <div className="sectionhead" style={{ marginTop: "22px", marginBottom: "12px" }}>
              <div>
                <div className="eyebrow">STEP 02</div>
                <h2>Search document evidence</h2>
              </div>
              <span className="pill">BM25 retrieval</span>
            </div>

            <div className="evidence-disclaimer">
              <ShieldCheck size={17} className="disclaimer-icon" />
              <div>
                <strong>Retrieved Source Evidence:</strong> The passages below are verbatim excerpts extracted directly from the document and ranked using BM25. These are <em>retrieved source passages, not AI-generated answers</em>.
              </div>
            </div>

            <form onSubmit={handleSearch} className="search-form">
              <div className="search-bar">
                <Search size={18} className="search-icon" />
                <input
                  type="text"
                  className="search-input"
                  placeholder="Ask a question or enter keywords (e.g. eligibility criteria, landholding, Aadhaar)..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  disabled={searchBusy}
                />
                <button type="submit" className="search-button" disabled={searchBusy || !query.trim()}>
                  {searchBusy ? "Searching…" : "Search"}
                </button>
              </div>
            </form>

            {searchError && (
              <div className="alert error">
                <AlertCircle size={17} />
                <div>{searchError}</div>
              </div>
            )}

            {searchBusy && (
              <div className="search-loading">
                <span className="muted">Retrieving most relevant source passages with BM25…</span>
              </div>
            )}

            {hasSearched && !searchBusy && searchResults && (
              <div className="search-results">
                {searchResults.results.length === 0 ? (
                  <div className="no-results">
                    <AlertCircle size={18} />
                    <span>No matching passages found for <em>"{searchResults.query}"</em>. Try different keywords or official scheme terms.</span>
                  </div>
                ) : (
                  <div className="results-list">
                    <div className="results-summary">
                      <b>Retrieved Source Passages ({searchResults.results.length} found)</b>
                      <span className="muted">Ranked by BM25 relevance score</span>
                    </div>
                    {searchResults.results.map((item) => (
                      <article className="evidence-card" key={item.chunk_id}>
                        <div className="evidence-meta">
                          <div className="evidence-badges">
                            <span className="badge page-badge">PAGE {item.page_number}</span>
                            <span className="badge chunk-badge">ID: {item.chunk_id}</span>
                          </div>
                          <span className="badge score-badge">BM25 Score: {item.score}</span>
                        </div>
                        <blockquote className="evidence-text">
                          {item.text}
                        </blockquote>
                      </article>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* EXTRACTED TEXT (Preserved) */}
          <div className="sectionhead extracted">
            <h2>Extracted text</h2>
            <span className="muted">Page-level output</span>
          </div>
          {result.pages.map((page) => (
            <article className="page" key={page.page_number}>
              <div className="eyebrow">PAGE {page.page_number}</div>
              <p>{page.text || "No selectable text found. OCR will be added in a later milestone."}</p>
            </article>
          ))}
        </section>
      )}

      <section className="next">
        <div className="eyebrow">COMING NEXT</div>
        <h2>Citizen assistance pipeline</h2>
        <div className="features">
          <Feature icon={<FileText />} title="Simplification" detail="Convert administrative language into plain English." />
          <Feature icon={<Languages />} title="Hindi translation" detail="Preserve important facts across languages." />
          <Feature
            icon={<Search />}
            title="Evidence-grounded Q&A"
            detail="BM25 passage retrieval active. AI-grounded synthesis with citations is planned next."
            status="BM25 Active · AI Planned"
          />
          <Feature icon={<ShieldCheck />} title="CDTM evaluation" detail="Inspect five dimensions and potential issues." />
        </div>
      </section>

      <footer>
        <span>CitizenAssist AI · Proof of concept</span>
        <span>Verify outputs against the original government source.</span>
      </footer>
    </main>
  );
}

function Feature({ icon, title, detail, status = "Planned" }) {
  return (
    <article className="feature">
      <span className="featureicon">{icon}</span>
      <h3>{title}</h3>
      <p>{detail}</p>
      <span className={`pill ${status.includes("Active") ? "active-pill" : ""}`}>{status}</span>
    </article>
  );
}
