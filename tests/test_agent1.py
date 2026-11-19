# ============================================================
# tests/test_agent1.py
# Wild Shield Karnataka — Agent 1 Unit Tests
#
# Tests all logic in Agent 1 without calling IBM Granite LLM.
# All LLM calls are bypassed via the fallback paths.
# ============================================================

import sys
import os
import unittest
import pandas as pd
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.agent1_risk import (
    RiskAssessmentAgent,
    RiskAssessmentResult,
    INCIDENT_FREQUENCY_SCORES,
    SPECIES_DANGER_SCORES,
    PROXIMITY_SCORES,
    RISK_THRESHOLDS,
    MAX_SCORE,
)


# ----------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------

def make_village_info(
    name="TestVillage",
    district="Mysuru",
    taluk="Hunsur",
    lat=12.26,
    lon=76.29,
    proximity_km=1.5,
):
    return {
        "village_name": name,
        "district": district,
        "taluk": taluk,
        "latitude": lat,
        "longitude": lon,
        "proximity_to_forest_km": proximity_km,
    }


def make_incidents(n=5, species="Elephant", severity="HIGH", days_ago_start=10):
    """Generate n synthetic incident rows."""
    rows = []
    base_date = date(2024, 11, 1)
    for i in range(n):
        rows.append({
            "village_name": "TestVillage",
            "district": "Mysuru",
            "taluk": "Hunsur",
            "latitude": 12.26 + i * 0.001,
            "longitude": 76.29 + i * 0.001,
            "species": species,
            "incident_type": "Crop Raid",
            "severity": severity,
            "incident_date": str(base_date - timedelta(days=days_ago_start + i)),
            "description": f"Test incident {i}",
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------
# Agent 1 Test Suite
# ----------------------------------------------------------------

class TestAgent1FrequencyAnalysis(unittest.TestCase):

    def setUp(self):
        self.agent = RiskAssessmentAgent()

    def test_empty_dataframe(self):
        """Empty DataFrame should return zeros."""
        result = self.agent._analyse_frequency(pd.DataFrame())
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["recent_30_days"], 0)
        self.assertEqual(result["monthly_counts"], {})

    def test_counts_total_incidents(self):
        """Should correctly count all incidents."""
        df = make_incidents(n=7)
        result = self.agent._analyse_frequency(df)
        self.assertEqual(result["total"], 7)

    def test_recent_30_days_detection(self):
        """Incidents within 30 days of the most recent should be flagged."""
        # 3 recent incidents (within 30 days) and 5 older ones
        recent = make_incidents(n=3, days_ago_start=5)   # 5-7 days ago
        old = make_incidents(n=5, days_ago_start=60)     # 60-64 days ago
        df = pd.concat([recent, old], ignore_index=True)
        result = self.agent._analyse_frequency(df)
        self.assertEqual(result["total"], 8)
        self.assertEqual(result["recent_30_days"], 3)

    def test_period_dates_set(self):
        """Period start and end dates should be populated."""
        df = make_incidents(n=3)
        result = self.agent._analyse_frequency(df)
        self.assertNotEqual(result["period_start"], "")
        self.assertNotEqual(result["period_end"], "")

    def test_monthly_counts_populated(self):
        """Monthly counts dict should have at least one entry."""
        df = make_incidents(n=5)
        result = self.agent._analyse_frequency(df)
        self.assertGreater(len(result["monthly_counts"]), 0)

    def test_invalid_dates_handled(self):
        """Rows with invalid dates should not crash frequency analysis."""
        df = make_incidents(n=3)
        df.loc[0, "incident_date"] = "not-a-date"
        # Should not raise
        result = self.agent._analyse_frequency(df)
        self.assertGreaterEqual(result["total"], 0)


class TestAgent1SpeciesAnalysis(unittest.TestCase):

    def setUp(self):
        self.agent = RiskAssessmentAgent()

    def test_empty_dataframe(self):
        result = self.agent._analyse_species(pd.DataFrame())
        self.assertEqual(result["top_species"], [])
        self.assertFalse(result["has_dangerous_species"])
        self.assertIsNone(result["most_dangerous"])

    def test_top_species_ranked_by_frequency(self):
        """Species with most incidents should be first in top_species."""
        rows = (
            [{"species": "Elephant", "incident_date": "2024-10-01"}] * 10 +
            [{"species": "Wild Boar", "incident_date": "2024-10-01"}] * 3
        )
        df = pd.DataFrame(rows)
        result = self.agent._analyse_species(df)
        self.assertEqual(result["top_species"][0], "Elephant")

    def test_dangerous_species_detected(self):
        """Tiger should be identified as the most dangerous species."""
        rows = [
            {"species": "Tiger", "incident_date": "2024-10-01"},
            {"species": "Wild Boar", "incident_date": "2024-10-01"},
        ]
        df = pd.DataFrame(rows)
        result = self.agent._analyse_species(df)
        self.assertTrue(result["has_dangerous_species"])
        self.assertEqual(result["most_dangerous"], "Tiger")

    def test_leopard_beats_elephant_in_danger(self):
        """Leopard (20pts) > Elephant (12pts) — danger ranking."""
        rows = [
            {"species": "Elephant", "incident_date": "2024-10-01"},
            {"species": "Leopard", "incident_date": "2024-10-01"},
        ]
        df = pd.DataFrame(rows)
        result = self.agent._analyse_species(df)
        self.assertEqual(result["most_dangerous"], "Leopard")

    def test_non_dangerous_species(self):
        """An unknown species should not trigger dangerous flag."""
        df = pd.DataFrame([{"species": "Peacock", "incident_date": "2024-10-01"}])
        result = self.agent._analyse_species(df)
        self.assertFalse(result["has_dangerous_species"])

    def test_max_five_top_species(self):
        """Should return at most 5 top species."""
        species_list = ["Elephant", "Leopard", "Tiger", "Wild Boar", "Gaur", "Bear", "Peacock"]
        rows = [{"species": s, "incident_date": "2024-10-01"} for s in species_list]
        df = pd.DataFrame(rows)
        result = self.agent._analyse_species(df)
        self.assertLessEqual(len(result["top_species"]), 5)


class TestAgent1RiskScoring(unittest.TestCase):

    def setUp(self):
        self.agent = RiskAssessmentAgent()

    def _run_score(self, n_incidents=0, days_recent=0, species="Wild Boar", proximity_km=10.0):
        """Helper: run scoring with controlled inputs."""
        total_df = make_incidents(n=n_incidents) if n_incidents > 0 else pd.DataFrame()
        freq = self.agent._analyse_frequency(total_df)
        # Override recent count for testing
        freq["recent_30_days"] = days_recent

        species_df = make_incidents(n=max(1, n_incidents), species=species) if n_incidents > 0 else pd.DataFrame()
        sp = self.agent._analyse_species(species_df)
        village_info = make_village_info(proximity_km=proximity_km)
        return self.agent._calculate_risk_score(freq, sp, village_info)

    def test_zero_incidents_scores_zero_frequency(self):
        """No incidents should give 0 frequency points."""
        _, _, breakdown = self._run_score(n_incidents=0)
        self.assertEqual(breakdown.get("incident_frequency", 0), 0)

    def test_high_incident_count_gives_max_frequency(self):
        """31+ incidents should give 55 frequency points."""
        total_df = make_incidents(n=35)
        freq = self.agent._analyse_frequency(total_df)
        sp = self.agent._analyse_species(total_df)
        _, _, breakdown = self.agent._calculate_risk_score(freq, sp, make_village_info())
        self.assertEqual(breakdown["incident_frequency"], 55)

    def test_recent_activity_adds_15_points(self):
        """Recent activity bonus should be exactly 15."""
        total_df = make_incidents(n=5, days_ago_start=5)
        freq = self.agent._analyse_frequency(total_df)
        sp = self.agent._analyse_species(total_df)
        _, _, breakdown = self.agent._calculate_risk_score(freq, sp, make_village_info())
        self.assertEqual(breakdown["recent_activity_bonus"], 15)

    def test_tiger_adds_25_species_points(self):
        """Tiger should contribute 25 species danger points."""
        df = make_incidents(n=5, species="Tiger")
        freq = self.agent._analyse_frequency(df)
        sp = self.agent._analyse_species(df)
        _, _, breakdown = self.agent._calculate_risk_score(freq, sp, make_village_info())
        self.assertEqual(breakdown["species_danger"], 25)

    def test_very_close_forest_adds_15_points(self):
        """Village within 2km of forest should get 15 proximity points."""
        df = make_incidents(n=3)
        freq = self.agent._analyse_frequency(df)
        sp = self.agent._analyse_species(df)
        _, _, breakdown = self.agent._calculate_risk_score(freq, sp, make_village_info(proximity_km=1.0))
        self.assertEqual(breakdown["forest_proximity"], 15)

    def test_score_never_exceeds_100(self):
        """Score should be capped at 100."""
        df = make_incidents(n=50, species="Tiger", days_ago_start=5)
        freq = self.agent._analyse_frequency(df)
        sp = self.agent._analyse_species(df)
        village = make_village_info(proximity_km=0.5)
        score, _, _ = self.agent._calculate_risk_score(freq, sp, village)
        self.assertLessEqual(score, 100.0)

    def test_factors_list_not_empty(self):
        """At least one risk factor should always be returned."""
        df = make_incidents(n=5)
        freq = self.agent._analyse_frequency(df)
        sp = self.agent._analyse_species(df)
        _, factors, _ = self.agent._calculate_risk_score(freq, sp, make_village_info())
        self.assertGreater(len(factors), 0)

    def test_scoring_breakdown_has_total(self):
        """Scoring breakdown must include a 'total' key."""
        df = make_incidents(n=5)
        freq = self.agent._analyse_frequency(df)
        sp = self.agent._analyse_species(df)
        _, _, breakdown = self.agent._calculate_risk_score(freq, sp, make_village_info())
        self.assertIn("total", breakdown)


class TestAgent1RiskClassification(unittest.TestCase):

    def setUp(self):
        self.agent = RiskAssessmentAgent()

    def test_low_risk_boundary(self):
        self.assertEqual(self.agent._classify_risk(0), "LOW")
        self.assertEqual(self.agent._classify_risk(30), "LOW")

    def test_medium_risk_boundary(self):
        self.assertEqual(self.agent._classify_risk(31), "MEDIUM")
        self.assertEqual(self.agent._classify_risk(65), "MEDIUM")

    def test_high_risk_boundary(self):
        self.assertEqual(self.agent._classify_risk(66), "HIGH")
        self.assertEqual(self.agent._classify_risk(100), "HIGH")

    def test_above_max_is_high(self):
        self.assertEqual(self.agent._classify_risk(999), "HIGH")


class TestAgent1HotspotDetection(unittest.TestCase):

    def setUp(self):
        self.agent = RiskAssessmentAgent()

    def test_empty_df_returns_village_coords(self):
        village = make_village_info(lat=12.5, lon=76.5)
        lat, lon = self.agent._identify_hotspot(pd.DataFrame(), village)
        self.assertAlmostEqual(lat, 12.5)
        self.assertAlmostEqual(lon, 76.5)

    def test_centroid_of_incidents(self):
        rows = [
            {"latitude": 12.0, "longitude": 76.0},
            {"latitude": 13.0, "longitude": 77.0},
        ]
        df = pd.DataFrame(rows)
        lat, lon = self.agent._identify_hotspot(df, make_village_info())
        self.assertAlmostEqual(lat, 12.5)
        self.assertAlmostEqual(lon, 76.5)

    def test_missing_coordinate_columns_falls_back(self):
        df = pd.DataFrame([{"species": "Elephant"}])
        village = make_village_info(lat=12.3, lon=76.3)
        lat, lon = self.agent._identify_hotspot(df, village)
        self.assertAlmostEqual(lat, 12.3)
        self.assertAlmostEqual(lon, 76.3)


class TestAgent1FallbackNarrative(unittest.TestCase):

    def setUp(self):
        self.agent = RiskAssessmentAgent()

    def test_fallback_narrative_returns_string(self):
        village = make_village_info()
        freq = {"total": 5, "recent_30_days": 2, "period_start": "", "period_end": ""}
        species = {"top_species": ["Elephant"], "most_dangerous": "Elephant"}
        narrative = RiskAssessmentAgent._fallback_narrative(village, freq, species, "HIGH")
        self.assertIsInstance(narrative, str)
        self.assertGreater(len(narrative), 50)

    def test_fallback_narrative_mentions_village(self):
        village = make_village_info(name="KodaguVillage")
        freq = {"total": 3, "recent_30_days": 0}
        species = {"top_species": ["Elephant"], "most_dangerous": "Elephant"}
        narrative = RiskAssessmentAgent._fallback_narrative(village, freq, species, "MEDIUM")
        self.assertIn("KodaguVillage", narrative)

    def test_fallback_narrative_mentions_risk_level(self):
        village = make_village_info()
        freq = {"total": 3, "recent_30_days": 0}
        species = {"top_species": ["Tiger"], "most_dangerous": "Tiger"}
        narrative = RiskAssessmentAgent._fallback_narrative(village, freq, species, "HIGH")
        self.assertIn("HIGH", narrative)


class TestAgent1FullAnalysis(unittest.TestCase):
    """Test the full analyse() method end-to-end (no LLM)."""

    def setUp(self):
        self.agent = RiskAssessmentAgent()

    def test_full_analysis_returns_result(self):
        df = make_incidents(n=5, species="Elephant")
        village = make_village_info()
        result = self.agent.analyse(df, village)
        self.assertIsInstance(result, RiskAssessmentResult)

    def test_full_analysis_success_flag(self):
        df = make_incidents(n=5)
        result = self.agent.analyse(df, make_village_info())
        self.assertTrue(result.success)

    def test_full_analysis_risk_level_valid(self):
        df = make_incidents(n=5)
        result = self.agent.analyse(df, make_village_info())
        self.assertIn(result.risk_level, ["LOW", "MEDIUM", "HIGH"])

    def test_full_analysis_score_in_range(self):
        df = make_incidents(n=5)
        result = self.agent.analyse(df, make_village_info())
        self.assertGreaterEqual(result.risk_score, 0)
        self.assertLessEqual(result.risk_score, 100)

    def test_full_analysis_empty_dataframe(self):
        """Empty DataFrame should not crash — should return LOW risk."""
        result = self.agent.analyse(pd.DataFrame(), make_village_info())
        self.assertIsInstance(result, RiskAssessmentResult)
        self.assertEqual(result.incident_count, 0)

    def test_full_analysis_to_dict_serializable(self):
        """to_dict() output must be JSON-serializable."""
        import json
        df = make_incidents(n=5)
        result = self.agent.analyse(df, make_village_info())
        # This should not raise
        json.dumps(result.to_dict())

    def test_high_risk_village_scores_correctly(self):
        """A village with many recent incidents + Tiger + close to forest should be HIGH."""
        df = make_incidents(n=20, species="Tiger", days_ago_start=5)
        village = make_village_info(proximity_km=0.8)
        result = self.agent.analyse(df, village)
        self.assertEqual(result.risk_level, "HIGH")
        self.assertGreaterEqual(result.risk_score, 66)

    def test_progress_callback_called(self):
        """Progress callback should be called at least once."""
        messages = []
        df = make_incidents(n=3)
        self.agent.analyse(df, make_village_info(), on_progress=messages.append)
        self.assertGreater(len(messages), 0)

    def test_primary_species_in_result(self):
        """Species from incidents should appear in result."""
        df = make_incidents(n=5, species="Leopard")
        result = self.agent.analyse(df, make_village_info())
        self.assertIn("Leopard", result.primary_species)

    def test_monthly_trend_is_dict(self):
        df = make_incidents(n=5)
        result = self.agent.analyse(df, make_village_info())
        self.assertIsInstance(result.monthly_trend, dict)

    def test_scoring_breakdown_has_all_components(self):
        df = make_incidents(n=5)
        result = self.agent.analyse(df, make_village_info())
        required = ["incident_frequency", "recent_activity_bonus", "species_danger", "forest_proximity"]
        for key in required:
            self.assertIn(key, result.scoring_breakdown, f"Missing key: {key}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
