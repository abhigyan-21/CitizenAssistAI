import { BookOpen } from "lucide-react";

export default function Masthead({ demoMode = false, onToggleDemoMode }) {
  return (
    <header className="masthead">
      <div className="masthead-inner">
        <div className="masthead-brand">
          <button
            type="button"
            className={`brand-mark ${demoMode ? "demo-active" : ""}`}
            onClick={onToggleDemoMode}
            title={demoMode ? "Demo Mode Active (Click to disable)" : "Click book icon to toggle Demo Mode"}
            aria-label="Toggle Demo Presentation Mode"
            style={{
              cursor: "pointer",
              border: demoMode ? "1px solid #16a34a" : "none",
              background: demoMode ? "rgba(22, 163, 74, 0.2)" : undefined,
              color: demoMode ? "#16a34a" : undefined,
              transition: "all 0.2s ease",
            }}
          >
            <BookOpen size={18} strokeWidth={2} />
          </button>
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
  );
}
