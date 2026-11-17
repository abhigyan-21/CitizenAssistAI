import { useState, useEffect } from "react";
import Masthead from "./components/Masthead";
import HeroSection from "./components/HeroSection";
import UploadPanel from "./components/UploadPanel";
import DocumentSummary from "./components/DocumentSummary";
import SearchPanel from "./components/SearchPanel";
import QAPanel from "./components/QAPanel";
import CDTMDashboard from "./components/CDTMDashboard";
import ExtractedPages from "./components/ExtractedPages";
import PhaseRoadmap from "./components/PhaseRoadmap";
import PhaseHeader from "./components/PhaseHeader";
import PhaseFooterNav from "./components/PhaseFooterNav";
import PhasePromptDocRequired from "./components/PhasePromptDocRequired";
import SemanticFidelityView from "./components/SemanticFidelityView";
import CrossLingualView from "./components/CrossLingualView";
import EvaluationEngineView from "./components/EvaluationEngineView";
import ComparativeShowcaseView from "./components/ComparativeShowcaseView";

const API = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function App() {
  // Navigation: 8-Phase Guided Walkthrough
  const [activePhase, setActivePhase] = useState(1);

  // Phase 01 — Upload & Extraction
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [showUploadFormInPhase1, setShowUploadFormInPhase1] = useState(false);

  // Phase 02 — BM25 Search
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState(null);
  const [searchBusy, setSearchBusy] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [hasSearched, setHasSearched] = useState(false);

  // Phase 03 & 08 — Q&A Dual-Paradigm
  const [mode, setMode] = useState("cdtm"); // "cdtm" | "basic"
  const [askQuery, setAskQuery] = useState("");
  const [qaResultCDTM, setQaResultCDTM] = useState(null);
  const [qaResultBasic, setQaResultBasic] = useState(null);
  const [qaBusy, setQaBusy] = useState(false);
  const [qaError, setQaError] = useState("");
  const [hasAsked, setHasAsked] = useState(false);
  const [highlightedChunkId, setHighlightedChunkId] = useState(null);

  // Phase 04 & 05 — Selected Chunk & Transformation State
  const [selectedChunkId, setSelectedChunkId] = useState("");
  const [simplificationResult, setSimplificationResult] = useState(null);
  const [translationResult, setTranslationResult] = useState(null);
  const [simplificationCount, setSimplificationCount] = useState(0);
  const [simplificationIssues, setSimplificationIssues] = useState(0);
  const [translationCount, setTranslationCount] = useState(0);
  const [translationIssues, setTranslationIssues] = useState(0);

  // Phase 06 & 07 — CDTM Evaluation Dashboard
  const [evaluationReport, setEvaluationReport] = useState(null);
  const [isRefreshingEval, setIsRefreshingEval] = useState(false);

  // Sync / preselect chunk priority:
  // 1. First cited chunk from recent Q&A response
  // 2. First available document chunk
  useEffect(() => {
    if (qaResultCDTM?.cited_chunk_ids?.length > 0) {
      setSelectedChunkId(qaResultCDTM.cited_chunk_ids[0]);
    } else if (!selectedChunkId && result?.chunks?.length > 0) {
      setSelectedChunkId(result.chunks[0].chunk_id);
    }
  }, [qaResultCDTM, result]);

  // --- Resets ---
  function resetSearch() {
    setQuery("");
    setSearchResults(null);
    setSearchError("");
    setHasSearched(false);
  }

  function resetQA() {
    setAskQuery("");
    setQaResultCDTM(null);
    setQaResultBasic(null);
    setQaError("");
    setHasAsked(false);
    setHighlightedChunkId(null);
  }

  function resetTransformations() {
    setSimplificationResult(null);
    setTranslationResult(null);
    setSelectedChunkId("");
    setSimplificationCount(0);
    setSimplificationIssues(0);
    setTranslationCount(0);
    setTranslationIssues(0);
  }

  async function fetchEvaluation(docId) {
    if (!docId) return;
    setIsRefreshingEval(true);
    try {
      const res = await fetch(`${API}/api/documents/${docId}/evaluation`);
      const data = await res.json();
      if (res.ok) {
        setEvaluationReport(data);
      }
    } catch {
      // Non-blocking dashboard fetch
    } finally {
      setIsRefreshingEval(false);
    }
  }

  // --- Handlers ---
  async function handleExtract(event) {
    event.preventDefault();
    if (!file) return setError("Select a PDF document first.");
    setBusy(true);
    setError("");
    setResult(null);
    setEvaluationReport(null);
    resetSearch();
    resetQA();
    resetTransformations();

    const body = new FormData();
    body.append("file", file);
    try {
      const res = await fetch(`${API}/api/documents/extract`, { method: "POST", body });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Extraction failed.");
      setResult(data);
      setShowUploadFormInPhase1(false);
      if (data.chunks?.length > 0) {
        setSelectedChunkId(data.chunks[0].chunk_id);
      }
      fetchEvaluation(data.document_id);
    } catch (err) {
      setError(err.message || "Could not connect to the backend.");
    } finally {
      setBusy(false);
    }
  }

  function handleFileChange(newFile) {
    setFile(newFile);
    setResult(null);
    setEvaluationReport(null);
    setError("");
    resetSearch();
    resetQA();
    resetTransformations();
  }

  async function handleSearch(event) {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return setSearchError("Please enter a query term.");
    if (!result?.document_id) return setSearchError("Please upload and extract a document first.");

    setSearchBusy(true);
    setSearchError("");
    try {
      const res = await fetch(`${API}/api/documents/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ document_id: result.document_id, query: trimmed, top_k: 5 }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Search failed.");
      setSearchResults(data);
      setHasSearched(true);
    } catch (err) {
      setSearchError(err.message || "Could not connect to the search endpoint.");
    } finally {
      setSearchBusy(false);
    }
  }

  async function handleAsk(event) {
    event.preventDefault();
    const trimmed = askQuery.trim();
    if (!trimmed) return setQaError("Please enter a question for the document.");
    if (!result?.document_id) return setQaError("Please upload and extract a document first.");

    setQaBusy(true);
    setQaError("");
    setHighlightedChunkId(null);

    try {
      // Execute fair comparison: same document, query, provider & model for both modes
      const [cdtmRes, basicRes] = await Promise.all([
        fetch(`${API}/api/documents/${result.document_id}/ask`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: trimmed, top_k: 5, mode: "cdtm" }),
        }),
        fetch(`${API}/api/documents/${result.document_id}/ask`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: trimmed, top_k: 5, mode: "basic" }),
        }),
      ]);

      const cdtmData = await cdtmRes.json();
      const basicData = await basicRes.json();

      if (!cdtmRes.ok) throw new Error(cdtmData.detail || "Failed to generate grounded answer.");

      setQaResultCDTM(cdtmData);
      if (basicRes.ok) {
        setQaResultBasic(basicData);
      } else {
        setQaResultBasic({
          answer: cdtmData.answer,
          mode: "basic",
          cited_chunk_ids: [],
          citations: [],
          retrieved_evidence: cdtmData.retrieved_evidence || [],
          provider_info: { ...cdtmData.provider_info, mode: "basic_unverified" },
        });
      }

      setHasAsked(true);

      // Pre-select first cited chunk if available
      if (cdtmData.cited_chunk_ids?.length > 0) {
        setSelectedChunkId(cdtmData.cited_chunk_ids[0]);
      }

      // Evaluate evidence grounding for CDTM-grounded answer
      try {
        const evalRes = await fetch(
          `${API}/api/documents/${result.document_id}/evaluation/grounding`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              answer: cdtmData.answer,
              cited_chunk_ids: cdtmData.cited_chunk_ids || [],
              insufficient_evidence: cdtmData.insufficient_evidence || false,
            }),
          }
        );
        const evalData = await evalRes.json();
        if (evalRes.ok) {
          setEvaluationReport((prev) =>
            prev ? { ...prev, evidence_grounding: evalData } : prev
          );
        }
      } catch {
        fetchEvaluation(result.document_id);
      }
    } catch (err) {
      setQaError(err.message || "Could not connect to the AI Q&A endpoint.");
    } finally {
      setQaBusy(false);
    }
  }

  function handleSimplificationComplete(simData) {
    setSimplificationResult(simData);
    setSimplificationCount((prev) => prev + 1);
    if (simData?.fidelity?.status === "potential_issue") {
      setSimplificationIssues((prev) => prev + 1);
    }
    if (result?.document_id) {
      fetchEvaluation(result.document_id);
    }
  }

  function handleTranslationComplete(transData) {
    setTranslationResult(transData);
    setTranslationCount((prev) => prev + 1);
    if (transData?.fidelity?.status === "potential_issue") {
      setTranslationIssues((prev) => prev + 1);
    }
    if (result?.document_id) {
      fetchEvaluation(result.document_id);
    }
  }

  function scrollToEvidence(chunkId) {
    setHighlightedChunkId(chunkId);
    setTimeout(() => {
      const el = document.getElementById(`evidence-${chunkId}`);
      if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 60);
  }

  const activeQaResult = mode === "basic" ? qaResultBasic : qaResultCDTM;

  return (
    <div className="app-canvas">
      <Masthead />

      {/* 8-Phase Guided Walkthrough Roadmap */}
      <PhaseRoadmap
        activePhase={activePhase}
        onSelectPhase={(phaseId) => setActivePhase(phaseId)}
        documentResult={result}
        hasSearched={hasSearched}
        hasAsked={hasAsked}
        simplificationResult={simplificationResult}
        translationResult={translationResult}
        evaluationReport={evaluationReport}
        qaResultBasic={qaResultBasic}
        qaResultCDTM={qaResultCDTM}
      />

      <main className="content-shell guided-content-shell">
        {/* Phase Header with Prev/Next buttons */}
        <PhaseHeader
          activePhase={activePhase}
          onPrevious={() => setActivePhase((p) => Math.max(1, p - 1))}
          onNext={() => setActivePhase((p) => Math.min(8, p + 1))}
          documentResult={result}
        />

        {/* Phase-Specific Content Shell */}
        <div className="phase-content-viewport">
          {/* If user navigates to Phases 2-8 without uploading a document */}
          {activePhase > 1 && !result ? (
            <PhasePromptDocRequired onGoToUpload={() => setActivePhase(1)} />
          ) : (
            <>
              {/* PHASE 1: Foundation — PDF Upload & Extraction */}
              {activePhase === 1 && (
                <div className="phase-view phase-1-view">
                  {!result ? (
                    <>
                      <HeroSection />
                      <UploadPanel
                        file={file}
                        busy={busy}
                        error={error}
                        onFileChange={handleFileChange}
                        onSubmit={handleExtract}
                      />
                    </>
                  ) : (
                    <div className="civic-card">
                      <DocumentSummary result={result} />

                      <div className="phase-reupload-bar">
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          onClick={() => setShowUploadFormInPhase1(!showUploadFormInPhase1)}
                        >
                          {showUploadFormInPhase1 ? "Hide Upload Form" : "Upload Another Document"}
                        </button>
                      </div>

                      {showUploadFormInPhase1 && (
                        <UploadPanel
                          file={file}
                          busy={busy}
                          error={error}
                          onFileChange={handleFileChange}
                          onSubmit={handleExtract}
                        />
                      )}

                      <ExtractedPages pages={result.pages} />
                    </div>
                  )}
                </div>
              )}

              {/* PHASE 2: Retrieval — BM25 Lexical Search */}
              {activePhase === 2 && (
                <div className="phase-view phase-2-view civic-card">
                  <SearchPanel
                    query={query}
                    onQueryChange={setQuery}
                    onSearch={handleSearch}
                    searchBusy={searchBusy}
                    searchError={searchError}
                    hasSearched={hasSearched}
                    searchResults={searchResults}
                    documentId={result.document_id}
                    filename={result.filename}
                  />
                </div>
              )}

              {/* PHASE 3: AI-Assisted Q&A (Evidence-Grounded) */}
              {activePhase === 3 && (
                <div className="phase-view phase-3-view civic-card">
                  <QAPanel
                    mode="cdtm"
                    askQuery={askQuery}
                    onAskQueryChange={setAskQuery}
                    onAsk={handleAsk}
                    qaBusy={qaBusy}
                    qaError={qaError}
                    hasAsked={hasAsked}
                    qaResult={qaResultCDTM}
                    highlightedChunkId={highlightedChunkId}
                    onScrollToEvidence={scrollToEvidence}
                    filename={result.filename}
                    documentId={result.document_id}
                    onOpenComparison={() => setActivePhase(8)}
                  />
                </div>
              )}

              {/* PHASE 4: Semantic Fidelity — Plain-Language Simplification */}
              {activePhase === 4 && (
                <div className="phase-view phase-4-view civic-card">
                  <SemanticFidelityView
                    documentId={result.document_id}
                    chunks={result.chunks || []}
                    selectedChunkId={selectedChunkId}
                    onSelectChunkId={setSelectedChunkId}
                    qaResult={qaResultCDTM}
                    simplificationResult={simplificationResult}
                    onSimplificationComplete={handleSimplificationComplete}
                    onNavigateToTranslation={() => setActivePhase(5)}
                  />
                </div>
              )}

              {/* PHASE 5: Cross-Lingual Fidelity — Hindi Translation */}
              {activePhase === 5 && (
                <div className="phase-view phase-5-view civic-card">
                  <CrossLingualView
                    documentId={result.document_id}
                    chunks={result.chunks || []}
                    selectedChunkId={selectedChunkId}
                    onSelectChunkId={setSelectedChunkId}
                    qaResult={qaResultCDTM}
                    translationResult={translationResult}
                    onTranslationComplete={handleTranslationComplete}
                    simplificationResult={simplificationResult}
                    onNavigateToSimplification={() => setActivePhase(4)}
                  />
                </div>
              )}

              {/* PHASE 6: CDTM Evaluation Engine */}
              {activePhase === 6 && (
                <div className="phase-view phase-6-view civic-card">
                  <EvaluationEngineView
                    documentId={result.document_id}
                    evaluationReport={evaluationReport}
                    onRefresh={() => fetchEvaluation(result.document_id)}
                    isRefreshing={isRefreshingEval}
                  />
                </div>
              )}

              {/* PHASE 7: CDTM Multidimensional Dashboard */}
              {activePhase === 7 && (
                <div className="phase-view phase-7-view civic-card">
                  <CDTMDashboard
                    documentId={result.document_id}
                    evaluationReport={evaluationReport}
                    onRefresh={() => fetchEvaluation(result.document_id)}
                    isRefreshing={isRefreshingEval}
                  />
                </div>
              )}

              {/* PHASE 8: Basic vs. CDTM Comparative Demonstration Showcase */}
              {activePhase === 8 && (
                <div className="phase-view phase-8-view civic-card">
                  <ComparativeShowcaseView
                    documentId={result.document_id}
                    question={askQuery}
                    basicResult={qaResultBasic}
                    cdtmResult={qaResultCDTM}
                    evaluationReport={evaluationReport}
                    retrievedEvidence={qaResultCDTM?.retrieved_evidence || []}
                    simplificationCount={simplificationCount}
                    simplificationIssues={simplificationIssues}
                    translationCount={translationCount}
                    translationIssues={translationIssues}
                    onGoToQA={() => setActivePhase(3)}
                  />
                </div>
              )}
            </>
          )}
        </div>

        {/* Phase Bottom Navigation CTA: Proceed to Next Phase */}
        <PhaseFooterNav
          activePhase={activePhase}
          onProceed={() => setActivePhase((p) => Math.min(8, p + 1))}
          onSelectPhase={(p) => setActivePhase(p)}
        />
      </main>

      <footer className="colophon">
        <div className="colophon-inner">
          <div className="colophon-main">
            <span className="colophon-title">CitizenAssist AI</span>
            <p className="colophon-text">
              An open-source research demonstrator for administrative document understanding and
              evidentiary grounding across five CDTM dimensions. Outputs must always be verified against
              official government portals.
            </p>
          </div>
          <div className="colophon-meta">
            <span>Reference Document: PM-KISAN Operational Guidelines</span>
            <span>Non-Governmental Academic &amp; Engineering Demonstrator</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
