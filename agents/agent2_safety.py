# ============================================================
# agents/agent2_safety.py
# Wild Shield Karnataka — Agent 2: Safety Advisor Agent
#
# PRIMARY RESPONSIBILITY:
#   Receive the structured RiskAssessmentResult from Agent 1 and
#   generate localized Kannada and English safety advisories for
#   villagers, farmers, livestock owners, and forest officials.
#
# LLM USED: IBM Granite LLM 2 (API Key 2)
#   Temperature: 0.7  (higher — natural, human-readable language)
#   Max tokens:  1500
#
# IMPORTANT:
#   This agent does NOT analyse raw incident data.
#   That is Agent 1's exclusive responsibility.
#   This agent NEVER claims to know real-time animal locations.
#   All advisories use pre-approved safety language templates
#   as guardrails before LLM enhancement.
# ============================================================

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional

from agents.agent1_risk import RiskAssessmentResult
from config.settings import get_llm_config_2

logger = logging.getLogger(__name__)

ProgressCallback = Optional[Callable[[str], None]]


# ================================================================
# Output Data Contract
# This typed dataclass is returned to the Orchestrator and
# displayed on the Streamlit dashboard.
# ================================================================
@dataclass
class SafetyAdvisoryResult:
    """
    Structured output from Agent 2.
    Contains Kannada and English advisories ready for the dashboard.

    Receives from Agent 1 (via Orchestrator):
        RiskAssessmentResult → risk_level, risk_score, primary_species,
        village_name, district, risk_factors
    """
    # Location (inherited from Agent 1)
    village_name: str
    district: str
    risk_level: str                      # Inherited from Agent 1
    risk_score: float                    # Inherited from Agent 1
    primary_species: list[str]           # Inherited from Agent 1

    # Advisory content
    advisory_english: str                # English safety advisory
    advisory_kannada: str                # Kannada safety advisory
    precautions: list[str]               # Bullet-point precautions
    target_audiences: list[str]          # Who this advisory is for

    # Metadata
    advisory_priority: str               # "URGENT" | "CAUTION" | "AWARENESS"
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    model_used: str = ""
    llm_available: bool = True
    success: bool = True
    error_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for DB storage and dashboard display."""
        return {
            "village_name": self.village_name,
            "district": self.district,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "primary_species": self.primary_species,
            "advisory_english": self.advisory_english,
            "advisory_kannada": self.advisory_kannada,
            "precautions": self.precautions,
            "target_audiences": self.target_audiences,
            "advisory_priority": self.advisory_priority,
            "generated_at": self.generated_at,
            "model_used": self.model_used,
            "llm_available": self.llm_available,
            "success": self.success,
            "error_message": self.error_message,
        }


# ================================================================
# Pre-Approved Advisory Templates
#
# These templates serve as safety guardrails.
# The LLM is prompted to enhance these — not replace them.
# This ensures no harmful, speculative, or irresponsible advice
# is generated regardless of LLM behaviour.
# ================================================================

ADVISORY_TEMPLATES: dict[str, dict] = {
    "LOW": {
        "priority": "AWARENESS",
        "english_base": (
            "Historical records indicate occasional wildlife activity in areas near {village}. "
            "This is a general awareness advisory based on past incident data. "
            "Residents are encouraged to remain alert, especially near forest edges, "
            "and to report any wildlife sightings to the local forest department."
        ),
        "precautions": [
            "Avoid walking alone near forest edges or agricultural fields after dark.",
            "Keep livestock secured in protected enclosures at night.",
            "Report any wildlife sightings to the Karnataka Forest Department.",
            "Do not leave food waste or garbage near your home — it may attract wildlife.",
            "Teach children not to approach or disturb wildlife.",
        ],
        "audiences": ["General public", "Villagers"],
    },

    "MEDIUM": {
        "priority": "CAUTION",
        "english_base": (
            "Historical data shows a moderate level of wildlife activity near {village}. "
            "Residents — particularly farmers and livestock owners — are advised to "
            "exercise increased caution when working near forest boundaries. "
            "Contact the forest department if you observe wildlife near your property."
        ),
        "precautions": [
            "Avoid agricultural fields and forest edges alone during early morning and evening.",
            "Travel in groups when going near forest boundaries.",
            "Secure all livestock in reinforced enclosures before nightfall.",
            "Install bright lights or noise deterrents around agricultural fields.",
            "Keep children indoors after sunset.",
            "Immediately report wildlife sightings to forest officials.",
            "Do NOT attempt to chase, trap, corner, or harm any wild animal.",
        ],
        "audiences": ["Farmers", "Livestock owners", "Villagers", "Forest officials"],
    },

    "HIGH": {
        "priority": "URGENT",
        "english_base": (
            "Historical records show a high frequency of wildlife incidents near {village}. "
            "Residents are strongly advised to exercise extreme caution at all times. "
            "Please contact the Karnataka Forest Department immediately if wildlife "
            "is observed near your village. Do NOT approach or provoke any wild animal."
        ),
        "precautions": [
            "URGENT: Contact the Karnataka Forest Department if wildlife is observed — 1800-425-7979.",
            "Do NOT go near forest edges, agricultural fields, or water sources alone.",
            "Keep all children and elderly persons indoors during dawn, dusk, and night hours.",
            "Move all livestock into reinforced, fully enclosed structures immediately.",
            "Organize community vigilance groups and alert neighbours.",
            "Use torches and make noise when moving outdoors after dark.",
            "Do NOT approach, corner, or provoke any wild animal under any circumstances.",
            "Block potential wildlife entry points to your property with appropriate fencing.",
            "Contact your Village Panchayat to coordinate with forest officials.",
        ],
        "audiences": [
            "All residents",
            "Farmers",
            "Livestock owners",
            "Forest officials",
            "Village Panchayat",
        ],
    },
}

# Pre-approved Kannada templates (used as fallback if LLM unavailable)
KANNADA_TEMPLATES: dict[str, str] = {
    "LOW": (
        "ಈ ಪ್ರದೇಶದಲ್ಲಿ ಅಲ್ಪ ಪ್ರಮಾಣದ ವನ್ಯಜೀವಿ ಚಟುವಟಿಕೆ ಐತಿಹಾಸಿಕ ದಾಖಲೆಗಳಲ್ಲಿ ಕಂಡುಬಂದಿದೆ. "
        "ಇದು ಸಾಮಾನ್ಯ ಜಾಗೃತಿ ಸಲಹೆಯಾಗಿದೆ. "
        "ನಿವಾಸಿಗಳು ಅರಣ್ಯ ಅಂಚಿನ ಬಳಿ ಎಚ್ಚರಿಕೆಯಿಂದ ಇರಬೇಕು ಮತ್ತು ಯಾವುದೇ "
        "ವನ್ಯಜೀವಿ ದರ್ಶನವಾದರೆ ಅರಣ್ಯ ಇಲಾಖೆಗೆ ತಿಳಿಸಬೇಕು."
    ),
    "MEDIUM": (
        "ಐತಿಹಾಸಿಕ ದಾಖಲೆಗಳ ಪ್ರಕಾರ ಈ ಗ್ರಾಮದ ಬಳಿ ಮಧ್ಯಮ ಪ್ರಮಾಣದ ವನ್ಯಜೀವಿ ಚಟುವಟಿಕೆ ಕಂಡುಬಂದಿದೆ. "
        "ರೈತರು ಮತ್ತು ಜಾನುವಾರು ಮಾಲೀಕರು ಅರಣ್ಯ ಅಂಚಿನ ಹೊಲಗಳಿಗೆ ಬೆಳಿಗ್ಗೆ ಮತ್ತು ಸಂಜೆ "
        "ಒಂಟಿಯಾಗಿ ಹೋಗಬಾರದು. "
        "ರಾತ್ರಿ ಎಲ್ಲ ಜಾನುವಾರುಗಳನ್ನು ಸುರಕ್ಷಿತ ಕೊಟ್ಟಿಗೆಯಲ್ಲಿ ಇರಿಸಿ. "
        "ಯಾವುದೇ ವನ್ಯಪ್ರಾಣಿ ಕಂಡರೆ ತಕ್ಷಣ ಅರಣ್ಯ ಇಲಾಖೆಗೆ ತಿಳಿಸಿ."
    ),
    "HIGH": (
        "ತುರ್ತು ಎಚ್ಚರಿಕೆ: ಐತಿಹಾಸಿಕ ದಾಖಲೆಗಳ ಪ್ರಕಾರ ಈ ಗ್ರಾಮದ ಬಳಿ ಅಧಿಕ ಪ್ರಮಾಣದ "
        "ವನ್ಯಜೀವಿ ಘಟನೆಗಳು ಕಂಡುಬಂದಿವೆ. "
        "ಅರಣ್ಯ ಅಂಚಿಗೆ ಒಂಟಿಯಾಗಿ ಅಥವಾ ರಾತ್ರಿ ಹೋಗಬೇಡಿ. "
        "ಮಕ್ಕಳು ಮತ್ತು ವೃದ್ಧರನ್ನು ಸೂರ್ಯಾಸ್ತದ ನಂತರ ಮನೆಯಲ್ಲಿರಿಸಿ. "
        "ಎಲ್ಲ ಜಾನುವಾರುಗಳನ್ನು ಭದ್ರವಾದ ಕೊಟ್ಟಿಗೆಯಲ್ಲಿ ಕೂಡಿ. "
        "ವನ್ಯಪ್ರಾಣಿ ಕಂಡರೆ ತಕ್ಷಣ ಅರಣ್ಯ ಇಲಾಖೆಯನ್ನು ಸಂಪರ್ಕಿಸಿ: 1800-425-7979. "
        "ಯಾವುದೇ ವನ್ಯಪ್ರಾಣಿಯನ್ನು ಓಡಿಸಲು, ಹಿಡಿಯಲು ಅಥವಾ ಹಿಂಸಿಸಲು ಪ್ರಯತ್ನಿಸಬೇಡಿ."
    ),
}

ADVISORY_DISCLAIMER_EN = (
    "\n\n⚠️ Note: This advisory is based on analysis of historical incident records only. "
    "It does not represent the confirmed current location or movement of any animal. "
    "For emergencies, contact Karnataka Forest Department: 1800-425-7979 (Toll-free)."
)

ADVISORY_DISCLAIMER_KN = (
    "\n\n⚠️ ಗಮನಿಸಿ: ಈ ಸಲಹೆಯು ಐತಿಹಾಸಿಕ ಘಟನೆಗಳ ದಾಖಲೆಗಳ ವಿಶ್ಲೇಷಣೆಯ ಆಧಾರದ ಮೇಲೆ ಮಾತ್ರ. "
    "ಯಾವುದೇ ಪ್ರಾಣಿಯ ಪ್ರಸ್ತುತ ಸ್ಥಳ ಅಥವಾ ಚಲನೆಯನ್ನು ಇದು ಸ್ಥಿರೀಕರಿಸುವುದಿಲ್ಲ. "
    "ತುರ್ತು ಸಂದರ್ಭದಲ್ಲಿ ಅರಣ್ಯ ಇಲಾಖೆಯನ್ನು ಸಂಪರ್ಕಿಸಿ: 1800-425-7979."
)


# ================================================================
# Safety Advisor Agent
# ================================================================
class SafetyAdvisorAgent:
    """
    Agent 2 — Safety Advisor Agent.

    Converts the RiskAssessmentResult from Agent 1 into localized
    Kannada and English safety advisories for affected communities.

    Design decisions:
    - Pre-approved templates are ALWAYS used as the foundation.
      The LLM enhances the language but does not change the safety message.
    - Two separate LLM calls: one for English, one for Kannada.
      This ensures quality in both languages independently.
    - Validation layer checks the advisory before returning it.
    - Robust fallback: if LLM fails, the template advisory is returned.
    """

    # Phrases that must NEVER appear in an advisory (safety validation)
    FORBIDDEN_PHRASES = [
        "current location",
        "currently located",
        "animal is at",
        "animal is near",
        "right now",
        "chase",
        "trap",
        "capture",
        "kill the animal",
        "harm the animal",
        "approach the animal",
        "GPS",
        "real-time",
        "live location",
    ]

    def __init__(self):
        self.config = get_llm_config_2()
        self._llm_client = None
        logger.info(
            "Agent 2 (Safety Advisor) initialized. Model: %s | Project: %s",
            self.config.model_id,
            self.config.project_id[:8] + "..." if self.config.project_id else "not set",
        )

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------

    def generate_advisory(
        self,
        risk_result: RiskAssessmentResult,
        on_progress: ProgressCallback = None,
    ) -> SafetyAdvisoryResult:
        """
        Main entry point called by the Orchestrator.

        Input:  RiskAssessmentResult from Agent 1
        Output: SafetyAdvisoryResult with Kannada + English advisories

        Pipeline:
          1. Validate input risk level
          2. Load pre-approved safety template for the risk level
          3. Generate enhanced English advisory using LLM 2
          4. Generate Kannada advisory using LLM 2
          5. Validate both advisories (safety check)
          6. Return structured SafetyAdvisoryResult
        """
        def _progress(msg: str):
            logger.info("Agent 2: %s", msg)
            if on_progress:
                on_progress(msg)

        village_name = risk_result.village_name
        risk_level = risk_result.risk_level

        _progress(
            f"Starting advisory generation for '{village_name}' "
            f"(Risk: {risk_level}, Score: {risk_result.risk_score})."
        )

        try:
            # ── Step 1: Validate risk level ──────────────────────────
            if risk_level not in ADVISORY_TEMPLATES:
                logger.warning(
                    "Agent 2: Unknown risk level '%s', defaulting to MEDIUM.", risk_level
                )
                risk_level = "MEDIUM"

            template = ADVISORY_TEMPLATES[risk_level]

            # ── Step 2: Generate English advisory ────────────────────
            _progress("Generating English advisory with IBM Granite LLM 2...")
            english_advisory, en_llm_ok = self._generate_english_advisory(
                risk_result, template
            )
            if en_llm_ok:
                _progress("English advisory generated via LLM.")
            else:
                _progress("English advisory using pre-approved template (LLM unavailable).")

            # ── Step 3: Generate Kannada advisory ────────────────────
            _progress("Generating Kannada advisory with IBM Granite LLM 2...")
            kannada_advisory, kn_llm_ok = self._generate_kannada_advisory(
                risk_result, template
            )
            if kn_llm_ok:
                _progress("Kannada advisory generated via LLM.")
            else:
                _progress("Kannada advisory using pre-approved template (LLM unavailable).")

            # ── Step 4: Safety validation ─────────────────────────────
            english_fallback = template["english_base"].format(village=village_name) + ADVISORY_DISCLAIMER_EN
            english_advisory = self._validate_advisory(english_advisory, english_fallback, "english")
            kannada_advisory  = self._validate_advisory(kannada_advisory, KANNADA_TEMPLATES[risk_level] + ADVISORY_DISCLAIMER_KN, "kannada")

            # ── Step 5: Build precautions and metadata ────────────────
            precautions = template["precautions"].copy()

            llm_available = en_llm_ok or kn_llm_ok

            result = SafetyAdvisoryResult(
                village_name=village_name,
                district=risk_result.district,
                risk_level=risk_level,
                risk_score=risk_result.risk_score,
                primary_species=risk_result.primary_species,
                advisory_english=english_advisory,
                advisory_kannada=kannada_advisory,
                precautions=precautions,
                target_audiences=template["audiences"],
                advisory_priority=template["priority"],
                model_used=self.config.model_id,
                llm_available=llm_available,
            )

            _progress(
                f"Advisory complete. Priority: {result.advisory_priority}. "
                f"LLM used: {llm_available}."
            )
            return result

        except Exception as exc:
            logger.error(
                "Agent 2 failed for '%s': %s", village_name, exc, exc_info=True
            )
            return self._error_result(risk_result, str(exc))

    def test_llm_connection(self) -> dict:
        """Test IBM Watsonx.ai connectivity for Agent 2."""
        try:
            llm = self._get_llm_client()
            response = llm.generate_text(
                prompt="Translate 'Stay safe' to Kannada in one sentence:"
            )
            return {
                "connected": True,
                "model": self.config.model_id,
                "platform": "IBM Watsonx.ai",
                "url": self.config.url,
                "test_response": response.strip() if response else "(empty)",
                "error": None,
            }
        except Exception as exc:
            return {
                "connected": False,
                "model": self.config.model_id,
                "platform": "IBM Watsonx.ai",
                "url": getattr(self.config, "url", ""),
                "test_response": None,
                "error": str(exc),
            }

    # ----------------------------------------------------------------
    # LLM Client — lazy initialization (IBM Watsonx.ai)
    # ----------------------------------------------------------------

    def _get_llm_client(self):
        """
        Initialize IBM Watsonx.ai ModelInference client for Agent 2 on first use.

        Agent 2 uses IBM Granite via Watsonx.ai — same platform as Agent 1.
        Uses WATSONX_API_KEY_2 / WATSONX_PROJECT_ID_2 (or falls back to Agent 1
        credentials if separate Agent 2 keys are not configured).
        Temperature 0.7 — higher than Agent 1 for natural advisory language.
        """
        if self._llm_client is not None:
            return self._llm_client

        from ibm_watsonx_ai import Credentials
        from ibm_watsonx_ai.foundation_models import ModelInference
        from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

        if not self.config.api_key or self.config.api_key.startswith("REPLACE"):
            raise ValueError(
                "WATSONX_API_KEY_2 (or WATSONX_API_KEY_1 as fallback) is not configured. "
                "Set it in your .env file or Streamlit Secrets."
            )
        if not self.config.project_id or self.config.project_id.startswith("REPLACE"):
            raise ValueError(
                "WATSONX_PROJECT_ID_2 (or WATSONX_PROJECT_ID_1 as fallback) is not configured. "
                "Set it in your .env file or Streamlit Secrets."
            )

        credentials = Credentials(
            url=self.config.url,
            api_key=self.config.api_key,
        )
        self._llm_client = ModelInference(
            model_id=self.config.model_id,
            credentials=credentials,
            project_id=self.config.project_id,
            params={
                GenParams.TEMPERATURE:    self.config.temperature,
                GenParams.MAX_NEW_TOKENS: self.config.max_new_tokens,
                GenParams.TOP_P:          self.config.top_p,
            },
        )
        logger.info(
            "Agent 2 Watsonx.ai client ready. Model: %s | Project: %s",
            self.config.model_id,
            self.config.project_id[:8] + "...",
        )
        return self._llm_client


    # ----------------------------------------------------------------
    # Advisory Generation
    # ----------------------------------------------------------------

    def _generate_english_advisory(
        self,
        risk_result: RiskAssessmentResult,
        template: dict,
    ) -> tuple[str, bool]:
        """
        Generate English advisory using LLM 2, grounded in the safety template.

        The template text is passed to the LLM as the base.
        The LLM is asked to make it more context-specific and readable —
        NOT to change the safety guidance.

        Returns: (advisory_text, llm_was_used)
        """
        try:
            llm = self._get_llm_client()

            species_str = (
                ", ".join(risk_result.primary_species)
                if risk_result.primary_species
                else "wildlife"
            )
            risk_factors_str = "\n".join(
                f"• {f}" for f in risk_result.risk_factors
            )
            base_advisory = template["english_base"].format(
                village=risk_result.village_name
            )

            prompt = (
                f"You are a Karnataka Forest Department wildlife safety officer.\n\n"
                f"Write a clear, compassionate safety advisory in ENGLISH for residents "
                f"of {risk_result.village_name} village, {risk_result.district} district.\n\n"
                f"=== RISK ASSESSMENT SUMMARY (from Risk Analysis Team) ===\n"
                f"Risk Level: {risk_result.risk_level}\n"
                f"Risk Score: {risk_result.risk_score}/100\n"
                f"Wildlife species involved: {species_str}\n"
                f"Historical incidents: {risk_result.incident_count}\n"
                f"Risk factors identified:\n{risk_factors_str}\n\n"
                f"=== BASE ADVISORY (approved safety template) ===\n"
                f"{base_advisory}\n\n"
                f"=== RULES YOU MUST FOLLOW ===\n"
                f"1. Use the base advisory as your foundation — do not contradict it.\n"
                f"2. Do NOT claim to know where any animal currently is.\n"
                f"3. Do NOT encourage people to approach, chase, trap, or harm wildlife.\n"
                f"4. Use simple, clear English — suitable for rural residents.\n"
                f"5. Keep the advisory to 3-4 sentences.\n"
                f"6. Do not add headers, bullet points, or section titles.\n\n"
                f"Write the safety advisory now:"
            )

            response = llm.generate_text(prompt=prompt)
            if response and response.strip():
                text = response.strip()
                return text + ADVISORY_DISCLAIMER_EN, True
            else:
                return base_advisory + ADVISORY_DISCLAIMER_EN, False

        except Exception as exc:
            logger.warning("Agent 2 English LLM call failed: %s", exc)
            base_advisory = template["english_base"].format(
                village=risk_result.village_name
            )
            return base_advisory + ADVISORY_DISCLAIMER_EN, False

    def _generate_kannada_advisory(
        self,
        risk_result: RiskAssessmentResult,
        template: dict,
    ) -> tuple[str, bool]:
        """
        Generate Kannada advisory using LLM 2.

        Uses the pre-approved Kannada template as the base.
        The LLM adapts it to be more context-specific for the village
        and species involved.

        Returns: (kannada_advisory_text, llm_was_used)
        """
        try:
            llm = self._get_llm_client()

            species_str = (
                ", ".join(risk_result.primary_species)
                if risk_result.primary_species
                else "ವನ್ಯಪ್ರಾಣಿ"
            )
            kannada_base = KANNADA_TEMPLATES.get(
                risk_result.risk_level, KANNADA_TEMPLATES["MEDIUM"]
            )
            english_base = template["english_base"].format(
                village=risk_result.village_name
            )

            prompt = (
                f"You are a Karnataka Forest Department wildlife safety officer.\n\n"
                f"Write a wildlife safety advisory in KANNADA for residents of "
                f"{risk_result.village_name} village in Karnataka.\n\n"
                f"=== INFORMATION ===\n"
                f"Risk level: {risk_result.risk_level}\n"
                f"Wildlife species involved: {species_str}\n\n"
                f"=== BASE ENGLISH ADVISORY ===\n"
                f"{english_base}\n\n"
                f"=== BASE KANNADA TEMPLATE ===\n"
                f"{kannada_base}\n\n"
                f"=== RULES ===\n"
                f"1. Write in simple Kannada that rural villagers can understand.\n"
                f"2. Mention the specific species: {species_str}.\n"
                f"3. Keep the same safety message as the English advisory.\n"
                f"4. Do NOT claim to know where any animal currently is.\n"
                f"5. Do NOT encourage approaching, chasing, or harming wildlife.\n"
                f"6. Write only the Kannada advisory — no English words, no headers.\n\n"
                f"ಕನ್ನಡ ಸಲಹೆ:"
            )

            response = llm.generate_text(prompt=prompt)
            if response and response.strip():
                text = response.strip()
                # Fallback to base if response is in English
                if self._is_mostly_english(text):
                    logger.warning(
                        "Agent 2: Replicate returned English instead of Kannada. Using template."
                    )
                    return KANNADA_TEMPLATES.get(risk_result.risk_level, KANNADA_TEMPLATES["MEDIUM"]) + ADVISORY_DISCLAIMER_KN, False
                return text + ADVISORY_DISCLAIMER_KN, True
            else:
                return KANNADA_TEMPLATES.get(risk_result.risk_level, KANNADA_TEMPLATES["MEDIUM"]) + ADVISORY_DISCLAIMER_KN, False

        except Exception as exc:
            logger.warning("Agent 2 Kannada LLM call failed: %s", exc)
            return KANNADA_TEMPLATES.get(risk_result.risk_level, KANNADA_TEMPLATES["MEDIUM"]) + ADVISORY_DISCLAIMER_KN, False

    # ----------------------------------------------------------------
    # Validation and Safety Checks
    # ----------------------------------------------------------------

    def _validate_advisory(
        self,
        advisory_text: str,
        fallback_text: str,
        lang: str,
    ) -> str:
        """
        Scan the generated advisory for forbidden phrases.
        If any forbidden content is found, the LLM output is replaced
        with the pre-approved template.

        This is the safety guardrail that prevents the LLM from
        making harmful or irresponsible claims.
        """
        advisory_lower = advisory_text.lower()
        for phrase in self.FORBIDDEN_PHRASES:
            if phrase.lower() in advisory_lower:
                logger.warning(
                    "Agent 2 safety validation: Forbidden phrase '%s' found in %s advisory. "
                    "Replacing with approved template.",
                    phrase,
                    lang,
                )
                return fallback_text
        return advisory_text

    @staticmethod
    def _is_mostly_english(text: str) -> bool:
        """
        Heuristic: check if a string is mostly ASCII (i.e., likely English).
        Kannada text has unicode characters in the range 0x0C80–0x0CFF.
        Returns True if fewer than 20% of characters are Kannada script.
        """
        if not text:
            return True
        kannada_chars = sum(
            1 for c in text if "\u0C80" <= c <= "\u0CFF"
        )
        return (kannada_chars / len(text)) < 0.10

    # ----------------------------------------------------------------
    # Error Result Factory
    # ----------------------------------------------------------------

    def _error_result(
        self,
        risk_result: RiskAssessmentResult,
        error_msg: str,
    ) -> SafetyAdvisoryResult:
        """Return safe fallback advisory when generation fails completely."""
        level = risk_result.risk_level if risk_result.risk_level in ADVISORY_TEMPLATES else "MEDIUM"
        template = ADVISORY_TEMPLATES[level]
        english = template["english_base"].format(
            village=risk_result.village_name
        ) + ADVISORY_DISCLAIMER_EN
        kannada = KANNADA_TEMPLATES.get(level, KANNADA_TEMPLATES["MEDIUM"]) + ADVISORY_DISCLAIMER_KN

        return SafetyAdvisoryResult(
            village_name=risk_result.village_name,
            district=risk_result.district,
            risk_level=level,
            risk_score=risk_result.risk_score,
            primary_species=risk_result.primary_species,
            advisory_english=english,
            advisory_kannada=kannada,
            precautions=template["precautions"],
            target_audiences=template["audiences"],
            advisory_priority=template["priority"],
            llm_available=False,
            success=False,
            error_message=error_msg,
        )
