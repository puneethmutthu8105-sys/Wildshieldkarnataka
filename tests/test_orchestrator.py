# ============================================================
# tests/test_orchestrator.py
# Wild Shield Karnataka — Orchestrator Integration Tests
#
# Tests the full two-agent pipeline end-to-end.
# No LLM calls are made — uses template fallbacks.
# ============================================================

import sys
import os
import unittest
import pandas as pd
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from orchestrator.orchestrator import WildShieldOrchestrator, AnalysisResult
from agents.agent1_risk import RiskAssessmentResult
from agents.agent2_safety import SafetyAdvisoryResult


class TestOrchestratorInit(unittest.TestCase):

    def test_orchestrator_instantiates(self):
        """Orchestrator should initialize without raising."""
        orch = WildShieldOrchestrator()
        self.assertIsNotNone(orch)
        self.assertIsNotNone(orch.agent1)
        self.assertIsNotNone(orch.agent2)


class TestOrchestratorDataLoading(unittest.TestCase):

    def setUp(self):
        self.orch = WildShieldOrchestrator()

    def test_get_all_incidents_returns_dataframe(self):
        df = self.orch.get_all_incidents()
        self.assertIsInstance(df, pd.DataFrame)

    def test_all_incidents_not_empty(self):
        """CSV has 45 synthetic incidents — should not be empty."""
        df = self.orch.get_all_incidents()
        self.assertGreater(len(df), 0)

    def test_all_incidents_has_required_columns(self):
        df = self.orch.get_all_incidents()
        required = ["village_name", "district", "species", "incident_date", "severity"]
        for col in required:
            self.assertIn(col, df.columns, f"Missing column: {col}")

    def test_all_incidents_all_synthetic(self):
        """All synthetic incidents should have is_synthetic = True (or 'TRUE')."""
        df = self.orch.get_all_incidents()
        if "is_synthetic" in df.columns:
            for val in df["is_synthetic"]:
                self.assertIn(str(val).upper(), ["TRUE", "1"],
                              f"Non-synthetic row found: {val}")

    def test_dashboard_stats_returns_dict(self):
        stats = self.orch.get_dashboard_stats()
        self.assertIsInstance(stats, dict)

    def test_dashboard_stats_has_required_keys(self):
        stats = self.orch.get_dashboard_stats()
        required = ["total_incidents", "villages_affected", "species_count"]
        for key in required:
            self.assertIn(key, stats)

    def test_dashboard_stats_total_incidents_correct(self):
        df = self.orch.get_all_incidents()
        stats = self.orch.get_dashboard_stats()
        self.assertEqual(stats["total_incidents"], len(df))

    def test_dashboard_stats_villages_affected_correct(self):
        df = self.orch.get_all_incidents()
        stats = self.orch.get_dashboard_stats()
        self.assertEqual(stats["villages_affected"], df["village_name"].nunique())


def _mock_llm_client():
    """Return a MagicMock LLM client that returns empty text (triggers template fallback)."""
    mock = MagicMock()
    mock.generate_text.return_value = ""
    return mock


_PATCH_A1 = patch(
    "agents.agent1_risk.RiskAssessmentAgent._get_llm_client",
    return_value=_mock_llm_client(),
)
_PATCH_A2 = patch(
    "agents.agent2_safety.SafetyAdvisorAgent._get_llm_client",
    return_value=_mock_llm_client(),
)


class TestOrchestratorPipeline(unittest.TestCase):

    def setUp(self):
        self.orch = WildShieldOrchestrator()

    def _run(self, village):
        return self.orch.run_full_analysis(village, use_db=False)

    @_PATCH_A1
    @_PATCH_A2
    def test_returns_analysis_result(self, _m2, _m1):
        result = self._run("Nagapura")
        self.assertIsInstance(result, AnalysisResult)

    @_PATCH_A1
    @_PATCH_A2
    def test_success_flag_true_for_known_village(self, _m2, _m1):
        result = self._run("Nagapura")
        self.assertTrue(result.success, f"Pipeline failed: {result.error_message}")

    @_PATCH_A1
    @_PATCH_A2
    def test_risk_assessment_is_result_type(self, _m2, _m1):
        result = self._run("Nagapura")
        self.assertIsInstance(result.risk_assessment, RiskAssessmentResult)

    @_PATCH_A1
    @_PATCH_A2
    def test_safety_advisory_is_result_type(self, _m2, _m1):
        result = self._run("Nagapura")
        self.assertIsInstance(result.safety_advisory, SafetyAdvisoryResult)

    @_PATCH_A1
    @_PATCH_A2
    def test_village_name_preserved(self, _m2, _m1):
        result = self._run("Nagapura")
        self.assertEqual(result.village_name, "Nagapura")

    @_PATCH_A1
    @_PATCH_A2
    def test_total_time_seconds_positive(self, _m2, _m1):
        result = self._run("Nagapura")
        self.assertGreater(result.total_time_seconds, 0)

    @_PATCH_A1
    @_PATCH_A2
    def test_risk_level_valid(self, _m2, _m1):
        result = self._run("Nagapura")
        self.assertIn(result.risk_assessment.risk_level, ["LOW", "MEDIUM", "HIGH", "UNKNOWN"])

    @_PATCH_A1
    @_PATCH_A2
    def test_advisory_priority_valid(self, _m2, _m1):
        result = self._run("Nagapura")
        self.assertIn(result.safety_advisory.advisory_priority, ["URGENT", "CAUTION", "AWARENESS"])

    @_PATCH_A1
    @_PATCH_A2
    def test_to_dict_json_serializable(self, _m2, _m1):
        import json
        result = self._run("Nagapura")
        # Should not raise
        json.dumps(result.to_dict())

    @_PATCH_A1
    @_PATCH_A2
    def test_all_11_villages_succeed(self, _m2, _m1):
        """Every village in the synthetic dataset should produce a valid result."""
        df = self.orch.get_all_incidents()
        villages = df["village_name"].unique().tolist()
        self.assertGreater(len(villages), 0)

        for village in villages:
            result = self._run(village)
            self.assertTrue(
                result.success,
                f"Pipeline failed for village '{village}': {result.error_message}"
            )
            self.assertIn(result.risk_assessment.risk_level, ["LOW", "MEDIUM", "HIGH"])
            self.assertIsInstance(result.safety_advisory.advisory_english, str)
            self.assertIsInstance(result.safety_advisory.advisory_kannada, str)

    @_PATCH_A1
    @_PATCH_A2
    def test_nagapura_is_high_risk(self, _m2, _m1):
        """Nagapura has 8 incidents with Elephant+Leopard close to forest → HIGH."""
        result = self._run("Nagapura")
        self.assertEqual(result.risk_assessment.risk_level, "HIGH",
                         f"Expected HIGH, got {result.risk_assessment.risk_level} "
                         f"(score: {result.risk_assessment.risk_score})")

    @_PATCH_A1
    @_PATCH_A2
    def test_progress_callback_invoked(self, _m2, _m1):
        """Progress callback should be called by orchestrator."""
        messages = []
        self.orch.run_full_analysis("Nagapura", use_db=False, on_progress=messages.append)
        self.assertGreater(len(messages), 0)

    @_PATCH_A1
    @_PATCH_A2
    def test_unknown_village_handled_gracefully(self, _m2, _m1):
        """An unknown village name should not crash — uses all CSV data as fallback."""
        result = self._run("CompletelyNonExistentVillage12345")
        # May succeed or return a result — must not raise
        self.assertIsInstance(result, AnalysisResult)

    @_PATCH_A1
    @_PATCH_A2
    def test_english_advisory_non_empty(self, _m2, _m1):
        result = self._run("Nagapura")
        self.assertGreater(len(result.safety_advisory.advisory_english), 50)

    @_PATCH_A1
    @_PATCH_A2
    def test_kannada_advisory_non_empty(self, _m2, _m1):
        result = self._run("Nagapura")
        self.assertGreater(len(result.safety_advisory.advisory_kannada), 20)

    @_PATCH_A1
    @_PATCH_A2
    def test_risk_factors_non_empty(self, _m2, _m1):
        result = self._run("Nagapura")
        self.assertGreater(len(result.risk_assessment.risk_factors), 0)

    @_PATCH_A1
    @_PATCH_A2
    def test_scoring_breakdown_has_total(self, _m2, _m1):
        result = self._run("Nagapura")
        self.assertIn("total", result.risk_assessment.scoring_breakdown)


class TestOrchestratorBatchAnalysis(unittest.TestCase):

    def setUp(self):
        self.orch = WildShieldOrchestrator()

    @_PATCH_A1
    @_PATCH_A2
    def test_batch_returns_list(self, _m2, _m1):
        results = self.orch.run_batch_analysis(["Nagapura", "Somvarpet"], use_db=False)
        self.assertIsInstance(results, list)

    @_PATCH_A1
    @_PATCH_A2
    def test_batch_returns_correct_count(self, _m2, _m1):
        villages = ["Nagapura", "Somvarpet", "Kabini Village"]
        results = self.orch.run_batch_analysis(villages, use_db=False)
        self.assertEqual(len(results), 3)

    @_PATCH_A1
    @_PATCH_A2
    def test_batch_preserves_order(self, _m2, _m1):
        villages = ["Nagapura", "Somvarpet"]
        results = self.orch.run_batch_analysis(villages, use_db=False)
        self.assertEqual(results[0].village_name, "Nagapura")
        self.assertEqual(results[1].village_name, "Somvarpet")


if __name__ == "__main__":
    unittest.main(verbosity=2)
