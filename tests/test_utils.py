# ============================================================
# tests/test_utils.py
# Wild Shield Karnataka — Utility Helper Tests
# ============================================================

import sys
import os
import unittest
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.helpers import (
    get_risk_color,
    get_species_emoji,
    format_risk_badge,
    format_priority_badge,
    calculate_incident_trends,
    calculate_species_distribution,
    calculate_village_risk_summary,
    prepare_map_data,
    SYNTHETIC_DATA_NOTICE,
)


def make_incident_df(n=10):
    rows = []
    for i in range(n):
        rows.append({
            "village_name": f"Village{i % 3}",
            "district": "Mysuru",
            "taluk": "Hunsur",
            "latitude": 12.26 + i * 0.001,
            "longitude": 76.29 + i * 0.001,
            "species": ["Elephant", "Leopard", "Wild Boar"][i % 3],
            "incident_type": "Crop Raid",
            "severity": ["HIGH", "MEDIUM", "LOW"][i % 3],
            "incident_date": f"2024-{(i % 3) + 9:02d}-{(i % 28) + 1:02d}",
        })
    return pd.DataFrame(rows)


class TestRiskColors(unittest.TestCase):

    def test_high_is_red(self):
        self.assertEqual(get_risk_color("HIGH"), "#dc2626")

    def test_medium_is_amber(self):
        self.assertEqual(get_risk_color("MEDIUM"), "#d97706")

    def test_low_is_green(self):
        self.assertEqual(get_risk_color("LOW"), "#16a34a")

    def test_unknown_is_gray(self):
        self.assertEqual(get_risk_color("UNKNOWN"), "#6b7280")

    def test_invalid_returns_gray(self):
        self.assertEqual(get_risk_color("WHATEVER"), "#6b7280")

    def test_case_insensitive(self):
        self.assertEqual(get_risk_color("high"), get_risk_color("HIGH"))


class TestSpeciesEmoji(unittest.TestCase):

    def test_elephant_emoji(self):
        self.assertEqual(get_species_emoji("elephant"), "🐘")

    def test_leopard_emoji(self):
        self.assertEqual(get_species_emoji("leopard"), "🐆")

    def test_tiger_emoji(self):
        self.assertEqual(get_species_emoji("tiger"), "🐅")

    def test_wild_boar_emoji(self):
        self.assertEqual(get_species_emoji("wild boar"), "🐗")

    def test_unknown_species_returns_default(self):
        result = get_species_emoji("peacock")
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)


class TestFormatBadges(unittest.TestCase):

    def test_high_badge_contains_color(self):
        badge = format_risk_badge("HIGH")
        self.assertIn("dc2626", badge)

    def test_medium_badge_contains_color(self):
        badge = format_risk_badge("MEDIUM")
        self.assertIn("d97706", badge)

    def test_low_badge_contains_color(self):
        badge = format_risk_badge("LOW")
        self.assertIn("16a34a", badge)

    def test_badge_contains_risk_level_text(self):
        badge = format_risk_badge("HIGH")
        self.assertIn("HIGH", badge)

    def test_priority_badge_urgent_red(self):
        badge = format_priority_badge("URGENT")
        self.assertIn("dc2626", badge)

    def test_priority_badge_caution_amber(self):
        badge = format_priority_badge("CAUTION")
        self.assertIn("d97706", badge)


class TestCalculateIncidentTrends(unittest.TestCase):

    def test_empty_df_returns_empty(self):
        result = calculate_incident_trends(pd.DataFrame())
        self.assertTrue(result.empty)

    def test_returns_dataframe_with_correct_columns(self):
        df = make_incident_df()
        result = calculate_incident_trends(df)
        self.assertIn("month", result.columns)
        self.assertIn("count", result.columns)

    def test_counts_are_positive(self):
        df = make_incident_df(n=10)
        result = calculate_incident_trends(df)
        self.assertTrue((result["count"] > 0).all())

    def test_total_matches_input_rows(self):
        df = make_incident_df(n=10)
        result = calculate_incident_trends(df)
        self.assertEqual(result["count"].sum(), 10)

    def test_missing_date_column_returns_empty(self):
        df = pd.DataFrame({"species": ["Elephant"]})
        result = calculate_incident_trends(df)
        self.assertTrue(result.empty)


class TestCalculateSpeciesDistribution(unittest.TestCase):

    def test_empty_returns_empty_dict(self):
        result = calculate_species_distribution(pd.DataFrame())
        self.assertEqual(result, {})

    def test_returns_dict(self):
        df = make_incident_df()
        result = calculate_species_distribution(df)
        self.assertIsInstance(result, dict)

    def test_all_species_present(self):
        df = make_incident_df(n=9)
        result = calculate_species_distribution(df)
        self.assertIn("Elephant", result)
        self.assertIn("Leopard", result)
        self.assertIn("Wild Boar", result)

    def test_counts_correct(self):
        rows = [{"species": "Elephant"}] * 5 + [{"species": "Tiger"}] * 3
        df = pd.DataFrame(rows)
        result = calculate_species_distribution(df)
        self.assertEqual(result["Elephant"], 5)
        self.assertEqual(result["Tiger"], 3)


class TestCalculateVillageRiskSummary(unittest.TestCase):

    def test_empty_returns_empty(self):
        result = calculate_village_risk_summary(pd.DataFrame())
        self.assertTrue(result.empty)

    def test_returns_dataframe(self):
        df = make_incident_df()
        result = calculate_village_risk_summary(df)
        self.assertIsInstance(result, pd.DataFrame)

    def test_has_village_name_column(self):
        df = make_incident_df()
        result = calculate_village_risk_summary(df)
        self.assertIn("village_name", result.columns)

    def test_has_incident_count_column(self):
        df = make_incident_df()
        result = calculate_village_risk_summary(df)
        self.assertIn("incident_count", result.columns)

    def test_village_counts_correct(self):
        rows = (
            [{"village_name": "A", "district": "D", "taluk": "T", "species": "Elephant"}] * 5 +
            [{"village_name": "B", "district": "D", "taluk": "T", "species": "Leopard"}] * 3
        )
        df = pd.DataFrame(rows)
        result = calculate_village_risk_summary(df)
        village_a = result[result["village_name"] == "A"]
        self.assertEqual(village_a["incident_count"].iloc[0], 5)


class TestPrepareMapData(unittest.TestCase):

    def test_empty_returns_empty_list(self):
        result = prepare_map_data(pd.DataFrame())
        self.assertEqual(result, [])

    def test_returns_list_of_dicts(self):
        df = make_incident_df()
        result = prepare_map_data(df)
        self.assertIsInstance(result, list)
        if result:
            self.assertIsInstance(result[0], dict)

    def test_each_point_has_coordinates(self):
        df = make_incident_df()
        result = prepare_map_data(df)
        for point in result:
            self.assertIn("latitude", point)
            self.assertIn("longitude", point)

    def test_missing_lat_lon_excluded(self):
        rows = [
            {"village_name": "V", "species": "E", "severity": "HIGH",
             "incident_date": "2024-10-01", "latitude": None, "longitude": None},
            {"village_name": "V", "species": "E", "severity": "HIGH",
             "incident_date": "2024-10-01", "latitude": 12.3, "longitude": 76.3},
        ]
        df = pd.DataFrame(rows)
        result = prepare_map_data(df)
        # Only the row with valid coordinates should appear
        self.assertEqual(len(result), 1)


class TestSyntheticDataNotice(unittest.TestCase):

    def test_notice_is_string(self):
        self.assertIsInstance(SYNTHETIC_DATA_NOTICE, str)

    def test_notice_mentions_synthetic(self):
        self.assertIn("synthetic", SYNTHETIC_DATA_NOTICE.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
