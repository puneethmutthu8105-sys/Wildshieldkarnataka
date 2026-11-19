# ============================================================
# orchestrator/orchestrator.py
# Wild Shield Karnataka — Agent Orchestrator
#
# PURPOSE:
#   Central controller that coordinates Agent 1 and Agent 2.
#
#   Workflow:
#     1. Fetch historical incident data from MySQL (or CSV fallback)
#     2. Pass data to Agent 1 (Risk Assessment)
#     3. Take Agent 1's structured RiskAssessmentResult
#     4. Pass it to Agent 2 (Safety Advisor)
#     5. Return combined AnalysisResult to the Streamlit dashboard
#     6. Save both agent outputs to the database (audit trail)
#
# ARCHITECTURE NOTE:
#   The Orchestrator is intentionally thin — it coordinates but
#   does not contain AI logic. All intelligence lives in the
#   individual agent classes.
# ============================================================

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional

import pandas as pd

from agents.agent1_risk import RiskAssessmentAgent, RiskAssessmentResult
from agents.agent2_safety import SafetyAdvisorAgent, SafetyAdvisoryResult
from database.connection import get_connection

logger = logging.getLogger(__name__)

# Progress callback type — allows Streamlit to show live status
ProgressCallback = Optional[Callable[[str], None]]


# ----------------------------------------------------------------
# Combined Output
# ----------------------------------------------------------------
@dataclass
class AnalysisResult:
    """
    Combined output from both agents.
    This is the final object returned to the Streamlit dashboard.
    """
    village_name: str
    district: str
    risk_assessment: RiskAssessmentResult
    safety_advisory: SafetyAdvisoryResult
    total_time_seconds: float
    success: bool
    error_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "village_name": self.village_name,
            "district": self.district,
            "risk_assessment": self.risk_assessment.to_dict(),
            "safety_advisory": self.safety_advisory.to_dict(),
            "total_time_seconds": round(self.total_time_seconds, 2),
            "success": self.success,
            "error_message": self.error_message,
        }


class WildShieldOrchestrator:
    """
    Central coordinator for Wild Shield Karnataka.

    Manages communication between Agent 1 and Agent 2,
    database reads/writes, and returns combined results to the UI.
    """

    def __init__(self):
        self.agent1 = RiskAssessmentAgent()
        self.agent2 = SafetyAdvisorAgent()
        logger.info("WildShield Orchestrator initialized with both agents.")

    # ----------------------------------------------------------------
    # Public API — called by Streamlit pages
    # ----------------------------------------------------------------

    def run_full_analysis(
        self,
        village_name: str,
        use_db: bool = True,
        on_progress: ProgressCallback = None,
    ) -> AnalysisResult:
        """
        Run the complete two-agent analysis pipeline for a village.

        Step-by-step workflow (visible in Streamlit's AI Agent Console):
          1. Load historical incidents (DB or CSV fallback)
          2. Agent 1: Risk Assessment
          3. Agent 2: Safety Advisory (using Agent 1's output)
          4. Save results to database
          5. Return combined AnalysisResult

        Args:
            village_name  : Village to analyse.
            use_db        : Use MySQL if True, CSV fallback if False.
            on_progress   : Callback(str) for live Streamlit status messages.

        Returns:
            AnalysisResult with both agent outputs.
        """
        def _progress(msg: str):
            logger.info("Orchestrator: %s", msg)
            if on_progress:
                on_progress(msg)

        start_time = datetime.now()
        _progress(f"Starting full analysis for '{village_name}'.")

        try:
            # ── Step 1: Load data ──────────────────────────────────────
            _progress("Loading historical incident data...")
            incidents_df, village_info = self._load_village_data(
                village_name, use_db=use_db
            )
            _progress(
                f"Loaded {len(incidents_df)} incident(s) for '{village_name}'."
            )

            # ── Step 2: Agent 1 ───────────────────────────────────────
            _progress("→ Agent 1 (Risk Assessment) starting...")

            def agent1_progress(msg: str):
                _progress(f"  [Agent 1] {msg}")

            risk_result = self.agent1.analyse(
                incidents_df, village_info, on_progress=agent1_progress
            )
            _progress(
                f"→ Agent 1 complete. Risk level: {risk_result.risk_level}, "
                f"Score: {risk_result.risk_score}/100."
            )

            # ── Step 3: Agent 2 ───────────────────────────────────────
            _progress("→ Passing Agent 1 output to Agent 2 (Safety Advisor)...")

            def agent2_progress(msg: str):
                _progress(f"  [Agent 2] {msg}")

            advisory_result = self.agent2.generate_advisory(
                risk_result, on_progress=agent2_progress
            )
            _progress(
                f"→ Agent 2 complete. Advisory priority: {advisory_result.advisory_priority}."
            )

            # ── Step 4: Save to database ──────────────────────────────
            if use_db:
                _progress("Saving results to database...")
                self._save_results(risk_result, advisory_result)

            elapsed = (datetime.now() - start_time).total_seconds()
            _progress(f"Full analysis complete in {elapsed:.2f} seconds.")

            return AnalysisResult(
                village_name=village_name,
                district=village_info.get("district", ""),
                risk_assessment=risk_result,
                safety_advisory=advisory_result,
                total_time_seconds=elapsed,
                success=True,
            )

        except Exception as exc:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(
                "Orchestrator: Analysis failed for '%s': %s",
                village_name, exc, exc_info=True,
            )
            return AnalysisResult(
                village_name=village_name,
                district="",
                risk_assessment=self._empty_risk_result(village_name),
                safety_advisory=self._empty_advisory_result(village_name),
                total_time_seconds=elapsed,
                success=False,
                error_message=str(exc),
            )

    def run_batch_analysis(
        self,
        village_names: list[str],
        use_db: bool = True,
        on_progress: ProgressCallback = None,
    ) -> list[AnalysisResult]:
        """
        Run analysis for multiple villages sequentially.
        Returns list of AnalysisResult objects in the same order.
        """
        results = []
        for i, name in enumerate(village_names, 1):
            if on_progress:
                on_progress(f"Processing village {i}/{len(village_names)}: {name}")
            result = self.run_full_analysis(name, use_db=use_db)
            results.append(result)
        return results

    def get_all_incidents(self) -> pd.DataFrame:
        """
        Fetch all historical incidents for dashboard display.
        Falls back to synthetic CSV if DB is unavailable.
        """
        try:
            conn = get_connection()
            if conn is None:
                logger.info("DB unavailable — loading incidents from CSV.")
                return self._get_synthetic_incidents()
            query = """
                SELECT id, village_name, district, taluk,
                       latitude, longitude, species, incident_type, severity,
                       description, incident_date, reported_by,
                       is_verified, is_synthetic
                FROM wildlife_incidents
                ORDER BY incident_date DESC
            """
            df = pd.read_sql(query, conn)
            conn.close()
            if df.empty:
                logger.info("DB has no incidents — loading from CSV.")
                return self._get_synthetic_incidents()
            return df
        except Exception as exc:
            logger.warning(
                "Orchestrator: DB incident fetch failed (%s) — using CSV.", exc
            )
            return self._get_synthetic_incidents()

    def get_dashboard_stats(self) -> dict:
        """Return summary statistics for the main dashboard KPI cards."""
        df = self.get_all_incidents()
        if df.empty:
            return {
                "total_incidents": 0,
                "villages_affected": 0,
                "species_count": 0,
                "high_risk_villages": 0,
                "medium_risk_villages": 0,
                "low_risk_villages": 0,
            }

        # Try DB risk counts first; fall back to estimating from incident frequency
        risk_counts = self._get_risk_counts()
        if not risk_counts:
            risk_counts = self._estimate_risk_counts_from_csv(df)

        return {
            "total_incidents": len(df),
            "villages_affected": int(df["village_name"].nunique()),
            "species_count": int(df["species"].nunique()),
            "high_risk_villages": risk_counts.get("HIGH", 0),
            "medium_risk_villages": risk_counts.get("MEDIUM", 0),
            "low_risk_villages": risk_counts.get("LOW", 0),
        }

    def test_connections(self) -> dict:
        """
        Test all external connections: DB, LLM 1, LLM 2.
        Returns a status report used by the sidebar and About page.
        """
        from database.connection import test_connection

        db_status = test_connection()
        llm1_status = self.agent1.test_llm_connection()
        llm2_status = self.agent2.test_llm_connection()

        return {
            "database": db_status,
            "llm1": llm1_status,
            "llm2": llm2_status,
        }

    # ----------------------------------------------------------------
    # Private Data Loading
    # ----------------------------------------------------------------

    def _load_village_data(
        self, village_name: str, use_db: bool
    ) -> tuple[pd.DataFrame, dict]:
        """Load incidents and village metadata for a village."""
        if use_db:
            conn = get_connection()
            if conn:
                try:
                    return self._load_from_db(conn, village_name)
                except Exception as exc:
                    logger.warning(
                        "DB village load failed (%s) — using CSV fallback.", exc
                    )

        return self._load_synthetic_data(village_name)

    def _load_from_db(self, conn, village_name: str) -> tuple[pd.DataFrame, dict]:
        """Load incidents and village info from MySQL."""
        incidents_query = """
            SELECT village_name, district, taluk, latitude, longitude,
                   species, incident_type, severity, description,
                   incident_date, is_verified, is_synthetic
            FROM wildlife_incidents
            WHERE LOWER(village_name) = LOWER(%s)
            ORDER BY incident_date DESC
        """
        df = pd.read_sql(incidents_query, conn, params=(village_name,))

        village_query = """
            SELECT village_name, taluk, district, latitude, longitude,
                   population, proximity_to_forest_km
            FROM villages
            WHERE LOWER(village_name) = LOWER(%s)
            LIMIT 1
        """
        village_df = pd.read_sql(village_query, conn, params=(village_name,))
        conn.close()

        if village_df.empty:
            village_info = {
                "village_name": village_name,
                "district": df["district"].iloc[0] if not df.empty else "",
                "taluk":    df["taluk"].iloc[0]    if not df.empty else "",
                "latitude":  float(df["latitude"].mean())  if not df.empty else 12.5,
                "longitude": float(df["longitude"].mean()) if not df.empty else 76.5,
                "proximity_to_forest_km": 3.0,
            }
        else:
            village_info = village_df.iloc[0].to_dict()
            # Ensure numeric types
            for key in ("latitude", "longitude", "proximity_to_forest_km"):
                if key in village_info:
                    try:
                        village_info[key] = float(village_info[key])
                    except (TypeError, ValueError):
                        village_info[key] = 12.5 if "lat" in key else (76.5 if "lon" in key else 3.0)

        return df, village_info

    def _load_synthetic_data(self, village_name: str) -> tuple[pd.DataFrame, dict]:
        """Load from the synthetic CSV when DB is unavailable."""
        import os
        csv_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "synthetic", "sample_incidents.csv"
        )
        try:
            full_df = pd.read_csv(csv_path)

            # Match village name (case-insensitive)
            village_df = full_df[
                full_df["village_name"].str.lower() == village_name.lower()
            ].copy()

            # If no matching village, use full dataset for demo purposes
            source_df = village_df if not village_df.empty else full_df

            village_info = {
                "village_name": village_name,
                "district":  source_df["district"].iloc[0]  if not source_df.empty else "Mysuru",
                "taluk":     source_df["taluk"].iloc[0]     if not source_df.empty else "Hunsur",
                "latitude":  float(source_df["latitude"].mean())  if not source_df.empty else 12.3,
                "longitude": float(source_df["longitude"].mean()) if not source_df.empty else 76.3,
                "proximity_to_forest_km": 2.5,
            }
            return source_df, village_info

        except Exception as exc:
            logger.error("Synthetic data load failed: %s", exc)
            return pd.DataFrame(), {
                "village_name": village_name,
                "district": "Unknown",
                "taluk": "Unknown",
                "latitude": 12.3,
                "longitude": 76.6,
                "proximity_to_forest_km": 5.0,
            }

    def _get_synthetic_incidents(self) -> pd.DataFrame:
        """Return all rows from the synthetic CSV."""
        import os
        csv_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "synthetic", "sample_incidents.csv"
        )
        try:
            return pd.read_csv(csv_path)
        except Exception as exc:
            logger.error("Cannot load synthetic CSV: %s", exc)
            return pd.DataFrame()

    def _get_risk_counts(self) -> dict[str, int]:
        """Count villages by risk level from the most recent assessments in DB."""
        try:
            conn = get_connection()
            if conn is None:
                return {}
            query = """
                SELECT risk_level, COUNT(DISTINCT village_name) as cnt
                FROM risk_assessments
                GROUP BY risk_level
            """
            df = pd.read_sql(query, conn)
            conn.close()
            return dict(zip(df["risk_level"], df["cnt"]))
        except Exception:
            return {}

    @staticmethod
    def _estimate_risk_counts_from_csv(df: pd.DataFrame) -> dict[str, int]:
        """
        Estimate risk level per village from incident counts when DB is offline.
        Uses the same thresholds as Agent 1's scoring logic:
          HIGH   : incident_count >= 6
          MEDIUM : 3 <= incident_count < 6
          LOW    : incident_count < 3
        This keeps the main dashboard KPI cards meaningful in fallback mode.
        """
        counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        if "village_name" not in df.columns:
            return counts
        per_village = df.groupby("village_name").size()
        for n in per_village:
            if n >= 6:
                counts["HIGH"] += 1
            elif n >= 3:
                counts["MEDIUM"] += 1
            else:
                counts["LOW"] += 1
        return counts

    # ----------------------------------------------------------------
    # Private Database Save
    # ----------------------------------------------------------------

    def _save_results(
        self,
        risk_result: RiskAssessmentResult,
        advisory_result: SafetyAdvisoryResult,
    ) -> None:
        """
        Persist both agent outputs to the database.
        This is non-critical — failures are logged but do not break the app.
        """
        import json
        try:
            conn = get_connection()
            if conn is None:
                logger.info("DB unavailable — skipping result save.")
                return

            cursor = conn.cursor()

            # Save risk assessment (Agent 1 output)
            cursor.execute(
                """
                INSERT INTO risk_assessments
                    (village_name, district, risk_score, risk_level, incident_count,
                     primary_species, risk_factors, analysis_summary,
                     assessed_at, agent1_model_used)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    risk_result.village_name,
                    risk_result.district,
                    risk_result.risk_score,
                    risk_result.risk_level,
                    risk_result.incident_count,
                    json.dumps(risk_result.primary_species),
                    json.dumps(risk_result.risk_factors),
                    risk_result.analysis_summary,
                    risk_result.assessed_at,
                    risk_result.model_used,
                ),
            )
            risk_id = cursor.lastrowid

            # Save safety advisory (Agent 2 output)
            cursor.execute(
                """
                INSERT INTO safety_advisories
                    (risk_assessment_id, village_name, district, advisory_en,
                     advisory_kn, priority, target_audience, precautions,
                     generated_at, agent2_model_used)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    risk_id,
                    advisory_result.village_name,
                    advisory_result.district,
                    advisory_result.advisory_english,
                    advisory_result.advisory_kannada,
                    advisory_result.advisory_priority,
                    json.dumps(advisory_result.target_audiences),
                    json.dumps(advisory_result.precautions),
                    advisory_result.generated_at,
                    advisory_result.model_used,
                ),
            )
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(
                "Orchestrator: Results saved. Risk ID: %d, Village: %s",
                risk_id, risk_result.village_name,
            )
        except Exception as exc:
            logger.warning("Orchestrator: DB save failed (non-critical): %s", exc)

    # ----------------------------------------------------------------
    # Empty Result Factories
    # ----------------------------------------------------------------

    @staticmethod
    def _empty_risk_result(village_name: str) -> RiskAssessmentResult:
        return RiskAssessmentResult(
            village_name=village_name, district="", taluk="",
            risk_score=0.0, risk_level="UNKNOWN", primary_species=[],
            incident_count=0, recent_incident_count=0, monthly_trend={},
            hotspot_lat=12.3, hotspot_lon=76.6, risk_factors=[],
            scoring_breakdown={},
            analysis_summary="Analysis unavailable.", data_period_start="",
            data_period_end="", llm_available=False,
            success=False, error_message="Orchestrator error.",
        )

    @staticmethod
    def _empty_advisory_result(village_name: str) -> SafetyAdvisoryResult:
        return SafetyAdvisoryResult(
            village_name=village_name, district="", risk_level="UNKNOWN",
            risk_score=0.0, primary_species=[],
            advisory_english="Advisory unavailable.",
            advisory_kannada="ಸಲಹೆ ಲಭ್ಯವಿಲ್ಲ.",
            precautions=[], target_audiences=[],
            advisory_priority="CAUTION",
            llm_available=False,
            success=False, error_message="Orchestrator error.",
        )
