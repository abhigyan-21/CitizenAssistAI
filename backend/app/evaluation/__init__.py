"""
CDTM Evaluation Package.
Exports all five evaluation dimensions and the unified evaluation engine.
"""
from app.evaluation.accessibility import (
    AccessibilityProxyMetrics,
    CitizenAccessibilityResult,
    evaluate_accessibility,
)
from app.evaluation.cross_lingual_fidelity import (
    CrossLingualFidelityResult,
    TranslationResponse,
)
from app.evaluation.engine import (
    CDTMReport,
    CDTMEvaluationEngine,
)
from app.evaluation.evidence_grounding import (
    ClaimSupportItem,
    EvidenceGroundingEvaluator,
    EvidenceGroundingResult,
)
from app.evaluation.semantic_fidelity import (
    SemanticFidelityResult,
    SimplificationResponse,
)
from app.evaluation.source_fidelity import (
    SourceFidelityResult,
    evaluate_source_fidelity,
)

__all__ = [
    "SourceFidelityResult",
    "evaluate_source_fidelity",
    "SemanticFidelityResult",
    "SimplificationResponse",
    "EvidenceGroundingResult",
    "ClaimSupportItem",
    "EvidenceGroundingEvaluator",
    "CrossLingualFidelityResult",
    "TranslationResponse",
    "CitizenAccessibilityResult",
    "AccessibilityProxyMetrics",
    "evaluate_accessibility",
    "CDTMReport",
    "CDTMEvaluationEngine",
]
