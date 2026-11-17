import { CheckCircle2, AlertCircle, FlaskConical } from "lucide-react";

/**
 * FidelityBadge
 *
 * Displays the AI-assisted semantic fidelity review result (Call 2).
 * Assesses ONLY whether meaning, conditions, amounts, dates and document
 * requirements were preserved in the simplified text.
 *
 * This badge is independent of SimplificationQualityBadge.
 * Do not merge the two results into a single verdict.
 *
 * Status values (from backend SemanticFidelityResult):
 *   verified              — Reviewer found no missing conditions or amounts.
 *   potential_issue       — Reviewer flagged one or more possibly missing items.
 *   requires_human_review — Reviewer was uncertain or the passage is complex.
 */

const STATUS_CONFIG = {
  verified: {
    className: "fidelity-badge fidelity-verified",
    icon: <CheckCircle2 size={13} strokeWidth={2} />,
    label: "Meaning Preserved",
  },
  potential_issue: {
    className: "fidelity-badge fidelity-issue",
    icon: <AlertCircle size={13} strokeWidth={2} />,
    label: "Potential Issue",
  },
  requires_human_review: {
    className: "fidelity-badge fidelity-review",
    icon: <AlertCircle size={13} strokeWidth={2} />,
    label: "Requires Human Review",
  },
};

export default function FidelityBadge({ status, controlled_demo }) {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.requires_human_review;

  return (
    <span className={config.className}>
      {config.icon}
      {config.label}
      {controlled_demo && (
        <span className="fidelity-demo-tag" title="Controlled failure demonstration — not a real failure">
          <FlaskConical size={11} strokeWidth={2} /> Demo
        </span>
      )}
    </span>
  );
}
