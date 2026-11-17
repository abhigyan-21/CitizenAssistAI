import { Search, AlertCircle } from "lucide-react";
import SearchResultCard from "./SearchResultCard";

export default function SearchPanel({
  query, onQueryChange, onSearch, searchBusy,
  searchError, hasSearched, searchResults,
  documentId, filename,
}) {
  return (
    <div className="search-section">
      <div className="card-header section-subhead">
        <div>
          <span className="card-step">PHASE 02</span>
          <h2 className="card-title">Document Evidence Retrieval</h2>
        </div>
        <span className="status-label">BM25 Lexical Ranking</span>
      </div>

      <div className="grounding-notice">
        <p>
          <strong>Notice on Retrieved Evidence:</strong> Direct textual retrieval from the uploaded
          administrative document via BM25.{" "}
          <em>These are retrieved source passages, not AI-generated answers.</em>
        </p>
      </div>

      <form onSubmit={onSearch} className="search-form">
        <div className="search-input-group">
          <Search size={18} className="search-icon" />
          <input
            type="text"
            className="search-field"
            placeholder="Enter query terms or scheme provisions (e.g., eligibility criteria, exclusion, landholder, DBT)..."
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            disabled={searchBusy}
          />
          <button type="submit" className="btn btn-secondary" disabled={searchBusy || !query.trim()}>
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
                <span className="evidence-criterion">Top-5 BM25 relevance scores</span>
              </div>
              {searchResults.results.map((item) => (
                <SearchResultCard
                  key={item.chunk_id}
                  item={item}
                  documentId={documentId}
                  filename={filename}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
