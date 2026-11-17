import { CheckCircle2, AlertCircle, Clock, FlaskConical } from "lucide-react";

/**
 * CrossLingualBadge
 *
 * Displays the Cross-Lingual Fidelity badge (CDTM Dimension d).
 *
 * Rule: Only show "Translation Preserved" (forest green) when BOTH checks
 * support verified fidelity:
 *   - term_preservation_status === "intact" (deterministic check)
 *   - fidelity.status === "verified" (Call 2 AI review pass)
 *
 * If either flags an issue: "Divergence Detected" (amber).
 * If either is uncertain: "Requires Human Review" (navy).
 */

export default function CrossLingualBadge({
  termStatus,
  fidelityStatus,
  controlledDemo = false,
}) {
  let badgeClass = "fidelity-badge fidelity-review";
  let icon = <Clock size={13} strokeWidth={2} />;
  let label = "Requires Human Review";

  if (termStatus === "intact" && fidelityStatus === "verified") {
    badgeClass = "fidelity-badge fidelity-verified";
    icon = <CheckCircle2 size={13} strokeWidth={2} />;
    label = "Translation Preserved";
  } else if (fidelityStatus === "potential_issue" || termStatus === "partial") {
    badgeClass = "fidelity-badge fidelity-issue";
    icon = <AlertCircle size={13} strokeWidth={2} />;
    label = "Divergence Detected";
  }

  return (
    <span className={badgeClass}>
      {icon}
      {label}
      {controlledDemo && (
        <span className="fidelity-demo-tag" title="Controlled failure demonstration — not a real failure">
          <FlaskConical size={11} strokeWidth={2} /> Demo
        </span>
      )}
    </span>
  );
}
