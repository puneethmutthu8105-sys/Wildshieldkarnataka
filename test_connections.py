# ============================================================
# test_connections.py
# Wild Shield Karnataka — Connection Tester
#
# Run this script to verify all external connections BEFORE
# running the full application:
#
#   python test_connections.py
#
# Tests:
#   1. MySQL database connection
#   2. IBM Granite LLM 1 (Agent 1 — API Key 1)
#   3. IBM Granite LLM 2 (Agent 2 — API Key 2)
# ============================================================

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import validate_config, get_llm_config_1, get_llm_config_2, get_db_config
from database.connection import test_connection
from agents.agent1_risk import RiskAssessmentAgent
from agents.agent2_safety import SafetyAdvisorAgent


def print_status(label: str, ok: bool, detail: str = ""):
    icon = "✅" if ok else "❌"
    print(f"  {icon}  {label}")
    if detail:
        print(f"       {detail}")


def main():
    print("\n" + "=" * 60)
    print("  🐘 WILD SHIELD KARNATAKA — Connection Tester")
    print("=" * 60)

    # ── 1. Configuration validation ───────────────────────────────
    print("\n📋 Configuration Check")
    cfg_result = validate_config()
    if cfg_result["valid"]:
        print_status("All environment variables configured", True)
    else:
        print_status("Configuration incomplete", False)
        for err in cfg_result["errors"]:
            print(f"       ⚠  {err}")
        print("\n  → Edit your .env file and add the missing values.")
        print("  → Then re-run this script.")

    # ── 2. Database connection ─────────────────────────────────────
    print("\n🗄️  MySQL Database")
    db_cfg = get_db_config()
    print(f"     Host:     {db_cfg.host}:{db_cfg.port}")
    print(f"     Database: {db_cfg.name}")
    print(f"     User:     {db_cfg.user}")
    db_result = test_connection()
    print_status(
        f"MySQL connection",
        db_result["connected"],
        f"Version: {db_result.get('version', 'N/A')}"
        if db_result["connected"]
        else f"Error: {db_result.get('error', 'unknown')}",
    )

    # ── 3. LLM 1 — Agent 1 ────────────────────────────────────────
    print("\n🤖 IBM Granite LLM 1 (Agent 1 — Risk Assessment)")
    llm1_cfg = get_llm_config_1()
    print(f"     Model: {llm1_cfg.model_id}")
    print(f"     URL:   {llm1_cfg.url}")
    print(f"     Temperature: {llm1_cfg.temperature}")

    if not llm1_cfg.api_key or llm1_cfg.api_key.startswith("REPLACE"):
        print_status("LLM 1 connection", False, "API Key not configured — skipping test.")
    else:
        print("     Testing connection (this may take 5-10 seconds)...")
        agent1 = RiskAssessmentAgent()
        llm1_result = agent1.test_llm_connection()
        print_status(
            "LLM 1 connection",
            llm1_result["connected"],
            f"Response: '{llm1_result.get('test_response', 'N/A')}'"
            if llm1_result["connected"]
            else f"Error: {llm1_result.get('error', 'unknown')}",
        )

    # ── 4. LLM 2 — Agent 2 (Replicate) ────────────────────────────
    print("\n🤖 IBM Granite LLM 2 via Replicate (Agent 2 — Safety Advisor)")
    llm2_cfg = get_llm_config_2()
    print(f"     Model:    {llm2_cfg.model_id}")
    print(f"     Platform: Replicate (https://replicate.com)")
    print(f"     Temperature: {llm2_cfg.temperature}")

    if not llm2_cfg.api_key or llm2_cfg.api_key.startswith("REPLACE"):
        print_status("LLM 2 (Replicate) connection", False, "REPLICATE_API_KEY not configured — skipping test.")
    else:
        print("     Testing connection (this may take 5-10 seconds)...")
        agent2 = SafetyAdvisorAgent()
        llm2_result = agent2.test_llm_connection()
        print_status(
            "LLM 2 (Replicate) connection",
            llm2_result["connected"],
            f"Response: '{llm2_result.get('test_response', 'N/A')}'"
            if llm2_result["connected"]
            else f"Error: {llm2_result.get('error', 'unknown')}",
        )

    # ── 5. Summary ─────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Next Steps:")
    if not db_result["connected"]:
        print("  1. Start MySQL and create the database:")
        print("     CREATE DATABASE wildshield_karnataka;")
        print("  2. Run:  python database/models.py")
        print("  3. Run:  python database/seed_data.py")
    print("  4. Run:  streamlit run app.py")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
