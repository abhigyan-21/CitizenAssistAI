import { CheckCircle2, AlertCircle, Clock, XCircle } from "lucide-react";

/**
 * SimplificationQualityBadge
 *
 * Displays the deterministic transformation-check result.
 * Maps directly to the four `simplification_quality` values the backend can return:
 *
 *   "simplified"            — Output is detectably different from the source.
 *   "insufficient"          — Output too similar; not meaningfully simplified.
 *   "requires_human_review" — Short passage; similarity score unreliable.
 *   "error"                 — Simplification call failed.
 *
 * This badge is independent of SemanticFidelity (FidelityBadge).
 * Never merge or combine the two into a single verdict.
 */

const QUALITY_CONFIG = {
  simplified: {
    className: "quality-badge quality-simplified",
    icon: <CheckCircle2 size={13} strokeWidth={2} />,
    label: "Successfully Simplified",
  },
  insufficient: {
    className: "quality-badge quality-insufficient",
    icon: <AlertCircle size={13} strokeWidth={2} />,
    label: "Insufficiently Simplified",
  },
  requires_human_review: {
    className: "quality-badge quality-review",
    icon: <Clock size={13} strokeWidth={2} />,
    label: "Requires Human Review",
  },
  error: {
    className: "quality-badge quality-error",
    icon: <XCircle size={13} strokeWidth={2} />,
    label: "Simplification Error",
  },
};

export default function SimplificationQualityBadge({ quality }) {
  const config = QUALITY_CONFIG[quality] ?? QUALITY_CONFIG.requires_human_review;

  return (
    <span className={config.className}>
      {config.icon}
      {config.label}
    </span>
  );
}
