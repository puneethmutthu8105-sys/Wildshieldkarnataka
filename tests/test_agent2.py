# ============================================================
# tests/test_agent2.py
# Wild Shield Karnataka — Agent 2 Unit Tests
#
# Tests all logic in Agent 2 without calling IBM Granite LLM.
# ============================================================

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.agent1_risk import RiskAssessmentResult
from agents.agent2_safety import (
    SafetyAdvisorAgent,
    SafetyAdvisoryResult,
    ADVISORY_TEMPLATES,
    KANNADA_TEMPLATES,
    ADVISORY_DISCLAIMER_EN,
    ADVISORY_DISCLAIMER_KN,
)


# ----------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------

def make_risk_result(
    village="TestVillage",
    district="Mysuru",
    taluk="Hunsur",
    risk_score=68.0,
    risk_level="HIGH",
    species=None,
    incident_count=8,
    recent_count=3,
    factors=None,
):
    """Build a mock RiskAssessmentResult for Agent 2 testing."""
    return RiskAssessmentResult(
        village_name=village,
        district=district,
        taluk=taluk,
        risk_score=risk_score,
        risk_level=risk_level,
        primary_species=species or ["Elephant", "Leopard"],
        incident_count=incident_count,
        recent_incident_count=recent_count,
        monthly_trend={"2024-10": 3, "2024-11": 5},
        hotspot_lat=12.26,
        hotspot_lon=76.29,
        risk_factors=factors or [
            "High incident frequency.",
            "Leopard sightings recorded.",
            "Village within 2km of forest.",
        ],
        scoring_breakdown={
            "incident_frequency": 25.0,
            "recent_activity_bonus": 15.0,
            "species_danger": 20.0,
            "forest_proximity": 15.0,
            "total": 68.0,
        },
        analysis_summary="High risk area with significant wildlife activity.",
        data_period_start="2024-07-01",
        data_period_end="2024-11-11",
        model_used="ibm/granite-13b-instruct-v2",
        llm_available=False,
    )


# ----------------------------------------------------------------
# Agent 2 Test Suite
# ----------------------------------------------------------------

class TestAgent2SafetyValidation(unittest.TestCase):
    """Test the safety validation guardrail."""

    def setUp(self):
        self.agent = SafetyAdvisorAgent()

    def test_safe_advisory_passes_validation(self):
        """A safe advisory should pass unchanged."""
        safe_text = "Residents should exercise caution near forest boundaries."
        result = self.agent._validate_advisory(safe_text, "fallback", "english")
        self.assertEqual(result, safe_text)

    def test_current_location_phrase_blocked(self):
        """'current location' should trigger replacement."""
        bad_text = "The leopard's current location is near the village."
        result = self.agent._validate_advisory(bad_text, "safe fallback", "english")
        self.assertEqual(result, "safe fallback")

    def test_chase_phrase_blocked(self):
        """'chase' should trigger replacement."""
        bad_text = "If you see a leopard, try to chase it away."
        result = self.agent._validate_advisory(bad_text, "safe fallback", "english")
        self.assertEqual(result, "safe fallback")

    def test_trap_phrase_blocked(self):
        """'trap' should trigger replacement."""
        bad_text = "You can trap the wild boar to protect your crops."
        result = self.agent._validate_advisory(bad_text, "safe fallback", "english")
        self.assertEqual(result, "safe fallback")

    def test_realtime_phrase_blocked(self):
        """'real-time' should trigger replacement."""
        bad_text = "Real-time tracking shows the elephant is here."
        result = self.agent._validate_advisory(bad_text, "safe fallback", "english")
        self.assertEqual(result, "safe fallback")

    def test_case_insensitive_detection(self):
        """Validation must be case-insensitive."""
        bad_text = "THE ANIMAL IS CURRENTLY LOCATED AT YOUR FARM."
        result = self.agent._validate_advisory(bad_text, "safe fallback", "english")
        self.assertEqual(result, "safe fallback")

    def test_fallback_text_returned_on_violation(self):
        """The exact fallback string should be returned, not the bad text."""
        bad = "Animal is currently located here."
        fallback = "APPROVED SAFETY MESSAGE"
        result = self.agent._validate_advisory(bad, fallback, "english")
        self.assertEqual(result, fallback)
        self.assertNotIn("currently located", result)


class TestAgent2KannadaDetection(unittest.TestCase):
    """Test the Kannada language detection heuristic."""

    def test_english_text_detected(self):
        """Pure English should be detected as not Kannada."""
        self.assertTrue(SafetyAdvisorAgent._is_mostly_english(
            "This is an English safety advisory for rural residents."
        ))

    def test_kannada_text_not_detected_as_english(self):
        """Kannada text should not be flagged as English."""
        kannada = "ಈ ಪ್ರದೇಶದಲ್ಲಿ ವನ್ಯಜೀವಿ ಚಟುವಟಿಕೆ ಕಂಡುಬಂದಿದೆ. ಎಚ್ಚರಿಕೆಯಿಂದ ಇರಿ."
        self.assertFalse(SafetyAdvisorAgent._is_mostly_english(kannada))

    def test_empty_string_is_english(self):
        """Empty string should be treated as English (safe fallback)."""
        self.assertTrue(SafetyAdvisorAgent._is_mostly_english(""))

    def test_mixed_text_with_mostly_kannada(self):
        """Text with >10% Kannada chars should not be flagged as English."""
        mixed = "ಎಚ್ಚರಿಕೆ: Residents ಅರಣ್ಯ ಅಂಚಿನ ಬಳಿ ಹೋಗಬೇಡಿ."
        self.assertFalse(SafetyAdvisorAgent._is_mostly_english(mixed))


class TestAgent2TemplateAdvisories(unittest.TestCase):
    """Test that pre-approved templates are present and valid."""

    def test_all_risk_levels_have_templates(self):
        """LOW, MEDIUM, HIGH must all have templates."""
        for level in ["LOW", "MEDIUM", "HIGH"]:
            self.assertIn(level, ADVISORY_TEMPLATES)
            self.assertIn(level, KANNADA_TEMPLATES)

    def test_templates_have_required_keys(self):
        """Each template must have priority, english_base, precautions, audiences."""
        required = ["priority", "english_base", "precautions", "audiences"]
        for level, template in ADVISORY_TEMPLATES.items():
            for key in required:
                self.assertIn(key, template, f"Missing '{key}' in {level} template")

    def test_priority_values_valid(self):
        """Priority must be URGENT, CAUTION, or AWARENESS."""
        valid_priorities = {"URGENT", "CAUTION", "AWARENESS"}
        for level, template in ADVISORY_TEMPLATES.items():
            self.assertIn(template["priority"], valid_priorities)

    def test_high_risk_is_urgent(self):
        """HIGH risk must map to URGENT priority."""
        self.assertEqual(ADVISORY_TEMPLATES["HIGH"]["priority"], "URGENT")

    def test_medium_risk_is_caution(self):
        self.assertEqual(ADVISORY_TEMPLATES["MEDIUM"]["priority"], "CAUTION")

    def test_low_risk_is_awareness(self):
        self.assertEqual(ADVISORY_TEMPLATES["LOW"]["priority"], "AWARENESS")

    def test_english_templates_have_village_placeholder(self):
        """English templates must have {village} placeholder for formatting."""
        for level, template in ADVISORY_TEMPLATES.items():
            self.assertIn("{village}", template["english_base"],
                          f"{level} template missing {{village}} placeholder")

    def test_precautions_not_empty(self):
        """Each template must have at least 3 precautions."""
        for level, template in ADVISORY_TEMPLATES.items():
            self.assertGreaterEqual(len(template["precautions"]), 3,
                                    f"{level} has fewer than 3 precautions")

    def test_kannada_templates_contain_kannada_script(self):
        """Kannada templates must contain actual Kannada characters."""
        for level, template in KANNADA_TEMPLATES.items():
            kannada_chars = sum(1 for c in template if "\u0C80" <= c <= "\u0CFF")
            self.assertGreater(kannada_chars, 10, f"{level} Kannada template has too few Kannada chars")

    def test_disclaimers_present(self):
        """Disclaimers must be non-empty strings."""
        self.assertIsInstance(ADVISORY_DISCLAIMER_EN, str)
        self.assertIsInstance(ADVISORY_DISCLAIMER_KN, str)
        self.assertGreater(len(ADVISORY_DISCLAIMER_EN), 50)
        self.assertGreater(len(ADVISORY_DISCLAIMER_KN), 20)


def _mock_llm_client():
    """Return a MagicMock LLM client that returns empty text (triggers template fallback)."""
    mock = MagicMock()
    mock.generate_text.return_value = ""
    return mock


class TestAgent2AdvisoryGeneration(unittest.TestCase):
    """Test generate_advisory() method end-to-end (no LLM — mocked)."""

    def setUp(self):
        self.agent = SafetyAdvisorAgent()

    @patch("agents.agent2_safety.SafetyAdvisorAgent._get_llm_client", return_value=_mock_llm_client())
    def test_returns_safety_advisory_result(self, _mock):
        risk = make_risk_result()
        result = self.agent.generate_advisory(risk)
        self.assertIsInstance(result, SafetyAdvisoryResult)

    @patch("agents.agent2_safety.SafetyAdvisorAgent._get_llm_client", return_value=_mock_llm_client())
    def test_village_name_propagated(self, _mock):
        risk = make_risk_result(village="KodaguVillage")
        result = self.agent.generate_advisory(risk)
        self.assertEqual(result.village_name, "KodaguVillage")

    @patch("agents.agent2_safety.SafetyAdvisorAgent._get_llm_client", return_value=_mock_llm_client())
    def test_risk_level_propagated(self, _mock):
        for level in ["LOW", "MEDIUM", "HIGH"]:
            risk = make_risk_result(risk_level=level)
            result = self.agent.generate_advisory(risk)
            self.assertEqual(result.risk_level, level)

    @patch("agents.agent2_safety.SafetyAdvisorAgent._get_llm_client", return_value=_mock_llm_client())
    def test_advisory_priority_matches_risk_level(self, _mock):
        """HIGH → URGENT, MEDIUM → CAUTION, LOW → AWARENESS."""
        expected = {"HIGH": "URGENT", "MEDIUM": "CAUTION", "LOW": "AWARENESS"}
        for risk_level, expected_priority in expected.items():
            risk = make_risk_result(risk_level=risk_level)
            result = self.agent.generate_advisory(risk)
            self.assertEqual(result.advisory_priority, expected_priority,
                             f"{risk_level} should give {expected_priority}")

    @patch("agents.agent2_safety.SafetyAdvisorAgent._get_llm_client", return_value=_mock_llm_client())
    def test_english_advisory_is_string(self, _mock):
        result = self.agent.generate_advisory(make_risk_result())
        self.assertIsInstance(result.advisory_english, str)

    @patch("agents.agent2_safety.SafetyAdvisorAgent._get_llm_client", return_value=_mock_llm_client())
    def test_kannada_advisory_is_string(self, _mock):
        result = self.agent.generate_advisory(make_risk_result())
        self.assertIsInstance(result.advisory_kannada, str)

    @patch("agents.agent2_safety.SafetyAdvisorAgent._get_llm_client", return_value=_mock_llm_client())
    def test_english_advisory_non_empty(self, _mock):
        result = self.agent.generate_advisory(make_risk_result())
        self.assertGreater(len(result.advisory_english), 50)

    @patch("agents.agent2_safety.SafetyAdvisorAgent._get_llm_client", return_value=_mock_llm_client())
    def test_kannada_advisory_non_empty(self, _mock):
        result = self.agent.generate_advisory(make_risk_result())
        self.assertGreater(len(result.advisory_kannada), 20)

    @patch("agents.agent2_safety.SafetyAdvisorAgent._get_llm_client", return_value=_mock_llm_client())
    def test_precautions_is_list(self, _mock):
        result = self.agent.generate_advisory(make_risk_result())
        self.assertIsInstance(result.precautions, list)
        self.assertGreater(len(result.precautions), 0)

    @patch("agents.agent2_safety.SafetyAdvisorAgent._get_llm_client", return_value=_mock_llm_client())
    def test_target_audiences_non_empty(self, _mock):
        result = self.agent.generate_advisory(make_risk_result())
        self.assertIsInstance(result.target_audiences, list)
        self.assertGreater(len(result.target_audiences), 0)

    @patch("agents.agent2_safety.SafetyAdvisorAgent._get_llm_client", return_value=_mock_llm_client())
    def test_unknown_risk_level_defaults_to_medium(self, _mock):
        """An unknown risk level should not crash — should default to MEDIUM."""
        risk = make_risk_result(risk_level="CATASTROPHIC")  # Not a valid level
        result = self.agent.generate_advisory(risk)
        self.assertEqual(result.risk_level, "MEDIUM")
        self.assertEqual(result.advisory_priority, "CAUTION")

    @patch("agents.agent2_safety.SafetyAdvisorAgent._get_llm_client", return_value=_mock_llm_client())
    def test_advisory_body_does_not_contain_harmful_phrases(self, _mock):
        """
        The advisory body (excluding the fixed disclaimer) must not contain
        harmful phrases like 'chase', 'trap', 'GPS', 'live location'.
        The disclaimer legitimately uses 'current location' to explain what
        the advisory is NOT about — that is correct safety language.
        """
        # Phrases that must NEVER appear in the advisory body
        harmful_phrases = [
            "chase", "trap", "capture", "kill the animal",
            "harm the animal", "approach the animal",
            "GPS", "live location",
        ]
        risk = make_risk_result()
        result = self.agent.generate_advisory(risk)

        # Check only the body before the disclaimer
        advisory_body = result.advisory_english.split("⚠️ Note:")[0].lower()
        for phrase in harmful_phrases:
            self.assertNotIn(
                phrase.lower(),
                advisory_body,
                f"Harmful phrase '{phrase}' found in English advisory body"
            )

    @patch("agents.agent2_safety.SafetyAdvisorAgent._get_llm_client", return_value=_mock_llm_client())
    def test_to_dict_is_json_serializable(self, _mock):
        """to_dict() must be JSON-serializable."""
        import json
        risk = make_risk_result()
        result = self.agent.generate_advisory(risk)
        json.dumps(result.to_dict())  # Should not raise

    @patch("agents.agent2_safety.SafetyAdvisorAgent._get_llm_client", return_value=_mock_llm_client())
    def test_progress_callback_called(self, _mock):
        """Progress callback should be called at least once."""
        messages = []
        risk = make_risk_result()
        self.agent.generate_advisory(risk, on_progress=messages.append)
        self.assertGreater(len(messages), 0)

    @patch("agents.agent2_safety.SafetyAdvisorAgent._get_llm_client", return_value=_mock_llm_client())
    def test_all_risk_levels_produce_valid_advisories(self, _mock):
        """All three risk levels must produce valid advisories."""
        for level in ["LOW", "MEDIUM", "HIGH"]:
            risk = make_risk_result(risk_level=level)
            result = self.agent.generate_advisory(risk)
            self.assertIsInstance(result.advisory_english, str)
            self.assertIsInstance(result.advisory_kannada, str)
            self.assertGreater(len(result.advisory_english), 10)
            self.assertGreater(len(result.advisory_kannada), 10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
