# agents/__init__.py
# Wild Shield Karnataka — Agents Package

from agents.agent1_risk import (
    RiskAssessmentAgent,
    RiskAssessmentResult,
    RISK_THRESHOLDS,
    SPECIES_DANGER_SCORES,
)
from agents.agent2_safety import (
    SafetyAdvisorAgent,
    SafetyAdvisoryResult,
    ADVISORY_TEMPLATES,
    KANNADA_TEMPLATES,
)

__all__ = [
    "RiskAssessmentAgent",
    "RiskAssessmentResult",
    "RISK_THRESHOLDS",
    "SPECIES_DANGER_SCORES",
    "SafetyAdvisorAgent",
    "SafetyAdvisoryResult",
    "ADVISORY_TEMPLATES",
    "KANNADA_TEMPLATES",
]
