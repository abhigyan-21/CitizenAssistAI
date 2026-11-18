import { useState } from "react";
import {
  ShieldCheck,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Info,
  FileCode,
} from "lucide-react";
import DimensionCard from "./DimensionCard";
import ResearchDemoControls from "./ResearchDemoControls";

/**
 * CDTMDashboard
 *
 * Full dashboard displaying independent evaluation results across the five
 * core dimensions of the Citizen Document Trustworthiness Model.
 *
 * Strict Research Invariant:
 * Evaluates all five dimensions independently without calculating any
 * composite, weighted average, ranking, or single overall trust score.
 */

export default function CDTMDashboard({
  documentId,
  evaluationReport,
  onRefresh,
  isRefreshing,
}) {
  const [collapsed, setCollapsed] = useState(false);
  const [showRawJson, setShowRawJson] = useState(false);

  return (
    <section className="cdtm-dashboard-container">
      {/* Dashboard Top Header */}
      <header className="cdtm-dashboard-header">
        <div className="cdtm-header-title-block">
          <div className="cdtm-icon-title-row">
            <ShieldCheck size={20} className="cdtm-shield-icon" />
            <h3 className="cdtm-main-title">CDTM Multidimensional Evaluation Dashboard</h3>
          </div>
          <p className="cdtm-header-subtitle">
            Independent evaluation of document understanding across the five Citizen Document Trustworthiness Model dimensions.
          </p>
        </div>

        <div className="cdtm-header-actions">
          <button
            type="button"
            className="btn-refresh-evaluation"
            onClick={onRefresh}
            disabled={isRefreshing || !documentId}
            title="Refresh multidimensional evaluation report from backend"
          >
            <RefreshCw size={13} className={isRefreshing ? "spin-icon" : ""} />
            {isRefreshing ? "Refreshing…" : "Refresh Evaluation"}
          </button>

          <button
            type="button"
            className="btn-collapse-dashboard"
            onClick={() => setCollapsed(!collapsed)}
            aria-expanded={!collapsed}
            title={collapsed ? "Expand Dashboard" : "Collapse Dashboard"}
          >
            {collapsed ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
          </button>
        </div>
      </header>

      {/* Prominent No-Composite-Score Banner */}
      <div className="no-composite-banner">
        <Info size={15} className="banner-info-icon" />
        <span>
          <strong>Strict CDTM Principle:</strong> Each dimension is evaluated independently.
          No composite or weighted trust score is calculated. Automated checks never substitute for human review.
        </span>
      </div>

      {!collapsed && (
        <div className="cdtm-dashboard-content">
          {/* Five Dimension Cards Grid */}
          <div className="dimension-cards-grid">
            {/* Dimension a: Source Fidelity */}
            <DimensionCard
              dimensionKey="source_fidelity"
              dimensionCode="Dim a"
              title="Source Fidelity"
              subtitle="Faithful preservation of source PDF structure and selectable text extraction."
              result={evaluationReport?.source_fidelity}
            />

            {/* Dimension b: Semantic Fidelity */}
            <DimensionCard
              dimensionKey="semantic_fidelity"
              dimensionCode="Dim b"
              title="Semantic Fidelity"
              subtitle="Preservation of original meaning, eligibility rules, and exclusions during simplification."
              result={evaluationReport?.semantic_fidelity}
            />

            {/* Dimension c: Evidence Grounding */}
            <DimensionCard
              dimensionKey="evidence_grounding"
              dimensionCode="Dim c"
              title="Evidence Grounding"
              subtitle="Claim-level corroboration of generated answers against verified source passages."
              result={evaluationReport?.evidence_grounding}
            />

            {/* Dimension d: Cross-Lingual Fidelity */}
            <DimensionCard
              dimensionKey="cross_lingual_fidelity"
              dimensionCode="Dim d"
              title="Cross-Lingual Fidelity"
              subtitle="Accurate translation to Hindi preserving administrative terminology, dates, and figures."
              result={evaluationReport?.cross_lingual_fidelity}
            />

            {/* Dimension e: Citizen Accessibility */}
            <DimensionCard
              dimensionKey="citizen_accessibility"
              dimensionCode="Dim e"
              title="Citizen Accessibility"
              subtitle="Automated structural readability proxies and detection of unexplained bureaucratic acronyms."
              result={evaluationReport?.citizen_accessibility}
            />
          </div>

          {/* Research Demonstration Controls */}
          <ResearchDemoControls documentId={documentId} />

          {/* Collapsible Raw API Report JSON */}
          {evaluationReport && (
            <div className="workbench-collapsible-section" style={{ marginTop: "16px" }}>
              <button
                type="button"
                className="btn-toggle-collapsible"
                onClick={() => setShowRawJson(!showRawJson)}
              >
                <FileCode size={14} />
                <span>Inspect Raw CDTM Evaluation Engine JSON Response</span>
                {showRawJson ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
              </button>

              {showRawJson && (
                <div className="collapsible-drawer-content">
                  <pre className="raw-json-block">
                    {JSON.stringify(evaluationReport, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}

          {/* Mandatory Methodological Disclaimer */}
          <footer className="cdtm-dashboard-footer">
            <p className="cdtm-disclaimer-text">
              <strong>Mandatory Research Disclaimer:</strong> AI-assisted evaluation requires human expert verification.
              Automated proxies do not constitute certified legal, administrative, or linguistic validation.
              Genuine Citizen Accessibility remains <em>not_evaluated</em> until verified via empirical citizen comprehension studies.
            </p>
          </footer>
        </div>
      )}
    </section>
  );
}
