import { BookOpen } from "lucide-react";

export default function Masthead() {
  return (
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
  );
}
