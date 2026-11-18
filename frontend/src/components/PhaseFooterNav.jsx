import { ArrowRight, RotateCcw } from "lucide-react";

const PROCEED_LABELS = {
  1: "Proceed to BM25 Retrieval →",
  2: "Proceed to AI-Assisted Q&A →",
  3: "Proceed to Semantic Fidelity →",
  4: "Proceed to Cross-Lingual Fidelity →",
  5: "Proceed to CDTM Evaluation Dashboard →",
  6: "Proceed to Basic vs CDTM Comparative Showcase →",
  7: "Restart Demonstration Walkthrough ↺",
};

export default function PhaseFooterNav({ activePhase, onProceed, onSelectPhase }) {
  const isFinal = activePhase === 7;
  const label = PROCEED_LABELS[activePhase] || "Next Phase →";

  return (
    <footer className="phase-footer-nav">
      <div className="phase-footer-left">
        <span className="phase-footer-step-note">
          Phase {activePhase} of 7 · Inspection View Active
        </span>
      </div>

      <div className="phase-footer-right">
        {isFinal ? (
          <button
            type="button"
            className="btn btn-proceed btn-restart"
            onClick={() => onSelectPhase(1)}
          >
            <RotateCcw size={15} />
            <span>Restart Demonstration Walkthrough</span>
          </button>
        ) : (
          <button
            type="button"
            className="btn btn-proceed"
            onClick={onProceed}
          >
            <span>{label}</span>
          </button>
        )}
      </div>
    </footer>
  );
}
